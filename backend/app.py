from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from flask import Flask, request
from flask_cors import CORS
import email
import email.header
import email.policy
import re

llm = Ollama(model="llama3")#, base_url="ollama:11434")
MAX_TOKENS = 4000
PROMPT_TOKENS = 0

# Preprocessing email
WHITELIST_HEADERS = ["Subject", "From", "sender", "References", "In-Reply-To", "Reply-To"]
REMOVE_TAGS_CONTENT = ["style", "script"]
REMOVE_TAGS = ["head", "meta", "html", "body", "div", "span", "table", "tbody", "tr", "td", "p", "br", "img", "b", "i", "hr"]
REMOVE_ATTRIBUTES = ["originalsrc", "shash", "style", "class", "id", "width", "height", "bgcolor", "border", "cellpadding", "cellspacing", "valign", "align", "colspan", "rowspan", "nowrap", "bordercolor", "bordercolorlight", "bordercolordark", "background", "background-color", "background-image", "background-repeat", "background-position", "background-size", "background-attachment"]

def preprocess_email(email):
    email_string = ""
    for header in email.items():
        skip = True 
        for keep_header in WHITELIST_HEADERS:
            if (header[0].lower() == keep_header.lower()):
                skip = False
                if ("phishing@pot" in header[1]):
                    skip = True
                break
        if not skip:
            email_string += header[0] + ": " + header[1] + "\n"
    email_string += "\n"

    body = email.get_body(preferencelist=('html', 'plain'))
    if (body == None):
        return
    payload = body.get_content()

    #remove unnecessary html tags by regex
    for tag in REMOVE_TAGS_CONTENT:
        payload = re.sub(r'<'+tag+r'.*?>.*?<\/'+tag+r'>', '', payload, flags=re.DOTALL)
    for tag in REMOVE_TAGS:
        payload = re.sub(r'<\/?'+tag+'.*?/?>', '', payload, flags=re.DOTALL)
    payload = re.sub(r'<[^/>][^>]*><\/[^>]+>', '', payload, flags=re.DOTALL) # empty tags

    # remove html comments
    payload = re.sub(r'<!--.*?-->', '', payload, flags=re.DOTALL)

    # remove unneccessary html attributes
    for attribute in REMOVE_ATTRIBUTES:
        payload = re.sub(r'<(.*?) '+attribute+r'="(.*?)"(.*?)>', r'<\1\3>', payload, flags=re.DOTALL)

    # remove unnecessary whitespace
    payload = re.sub(r'\s+$', '', payload, flags=re.MULTILINE)
    payload = re.sub(r'^\s+', '', payload, flags=re.MULTILINE)
    payload = re.sub(r'\n+', '\n', payload)

    email_string += payload

    # trim the email + prompt template to fit within the 1024 token limit
    while (llm.get_num_tokens(email_string) > MAX_TOKENS-PROMPT_TOKENS):
        email_string = email_string[:-1]

    return email_string

# Create llm-chain for main analysis
main_template = """### Instruction:
### Instruction:
Act as a phishing detector for someone who is not familiar with cybersecurity.
Examine the email and look for signs of phishing or legitimacy.
Identify and list the key elements that help you determine the legitimacy of the email.
Phishing emails often impesonate well-known brrands and use social engineering tactics to trick the recipient.
These tactics may involve fake rewards, false warnings about account issues and creating a sense of urgency.
Common tactics also include spoofing email addresses and using deceptive links.
To analyze the email follow the steps below:
1. Identify any impersonation of well-known brands.
2. Examine the email header for spoofing indicators, such as inconsistencies in the sender name or email address.
3. Assess the subject line for typical phishing traits (e.g., urgency, promises of rewards).
4. Analyze the email body for social engineering techniques aimed at prompting clicks on hyperlinks. Inspect URLs to determine if they are misleading or lead to suspicious websites. Remember that even legitimate emails may use tracking links.
Start by providing a list of the key elements that help you determine the legitimacy of the email.
Then, provide a summary of your findings and give a final verdict on whether the email is a phishing attempt or a legitimate email.
Remember that marketing emails may in some cases use similar tactics.

You only analyze whether the email is a phishing attempt or a legitimate email. You do not flag any other types of spam as phishing.
You apply critical thinking to reason about whether these tactics are a sign of phishing or if there is a legitimate reason for them.

### Examples:
## Example 1:
# Email:
From: Laura Moore <ugxjumoorelaura@gmail.com>
Subject: The main thing is to have time to withdraw your +12,695$

You joined our automatic Bitcoin earning platform 364 days ago.
Your account has been earning funds through its automatic earning
capabilities, accumulating $25.745 over the past year.
Your account will be blocked shortly. Withdraw your remaining funds immediately.
Access to your account can be gained by following the instructions in
the attached PDF.

# Response:
This email exhibits several signs of phishing:
1. The sender's email address does not match the official domain of the company.
2. The subject line creates a sense of urgency and promises a large reward.
3. The email threatens account blockage to prompt immediate action.
4. The attachment may contain malware or malicious links.
Based on these factors, the email is likely a phishing attempt.

## Example 2:
# Email:
From: Newspaper Times <newsletter@newstimes.com>
Subject: Subscription Billing Problem

Dear Subscriber,
We have encountered an issue with your subscription billing.
Please update your payment information to avoid service disruption.
<a href="https://www.newstimes.com/billing?id=ndfh4237dsafdjnw34sl">Update Payment Information</a>

# Response:
This email appears legitimate:
1. The sender's email address matches the official domain of the company.
2. The subject line addresses a common issue with subscriptions.
3. The email provides a clear call-to-action without creating a sense of urgency.
4. The hyperlink leads to the official website of the company.
Based on these factors, the email is likely legitimate.

### Email:
{email}

### Response:
"""

PROMPT_TOKENS = llm.get_num_tokens(main_template)

parser = StrOutputParser()

main_prompt = PromptTemplate(
    template=main_template,
    input_variables=["email"],
)

main_chain = main_prompt | llm | parser

# Create llm-chain for output formatting
format_template = """
### Instruction:
Act as a formatter that takes in natural language data and formats in into a specific JSON-format.
The input will contain a summary of an email and a verdict on whether it is a phishing attempt or a legitimate email.
It will also contain a list of key elements that help determine the legitimacy of the email.
You will output a score indicating how sure you are that the email is a phishing attempt or a legitimate email, where 1 indicates a phishing attempt and 0 indicates a legitimate email. 
The output will also contain a list of the reasons given for the verdict.

### Format instructions:
{format_instructions}

### Input:
{input}

### Response:
"""

class PhishingVerdict(BaseModel):
    reasons: List[str] = Field(description="A list of reasons why the email is or is not a phishing attempt")
    phishing_score: float = Field(description="A likelyhood from 0 to 1 that the email is a phishing attempt")

format_parser = JsonOutputParser(pydantic_object=PhishingVerdict)

format_prompt = PromptTemplate(
    template=format_template,
    input_variables=["input"],
    partial_variables={"format_instructions": format_parser.get_format_instructions()}
)

format_chain = format_prompt | llm | format_parser


def get_email_score(preprocessed_email):
    response = main_chain.invoke({
        "email": preprocessed_email
    })
    formatted = {}
    while ("phishing_score" not in formatted or "reasons" not in formatted):
        formatted = format_chain.invoke({
            "input": response
        })
    formatted["response"] = response
    return formatted

# Web server
app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/analyze-email", methods=["POST"])
def analyze_email():
    parsed_email = email.message_from_string(request.json["email"], policy=email.policy.default)
    #response = {'reasons': ["The sender's email address appears legitimate.", "The subject line is generic and doesn't create a sense of urgency.", 'The email body contains information about Abakus and job listings without any social engineering tactics.', 'The hyperlinks provided lead to the official website of Abakus.'], 'phishing_score': 0, 'response': 'I\'ll analyze the email and provide a list of key elements that help determine its legitimacy.\n\n**Key Elements:**\n\n1. **Sender\'s Email Address**: Is it a legitimate domain or a generic email address?\n2. **Subject Line**: Does it create a sense of urgency, promise rewards, or use misleading language?\n3. **Email Body**: Are there any social engineering tactics aimed at prompting clicks on hyperlinks?\n4. **Hyperlinks**: Do they lead to suspicious websites or contain misleading URLs?\n5. **Attachments**: Are they legitimate and necessary for the email\'s purpose?\n\nNow, let\'s analyze the email:\n\n**Subject Line**: "Ukesmail uke 21" is a generic subject line that doesn\'t raise any red flags.\n\n**Sender\'s Email Address**: The sender\'s address is `no-reply@abakus.no`, which appears to be a legitimate domain for Abakus.\n\n**Email Body**: The email contains job listings and information about Abakus, but there are no social engineering tactics or misleading language used.\n\n**Hyperlinks**: The hyperlinks provided lead to the official website of Abakus (`https://abakus.no`) and appear to be legitimate.\n\n**Attachments**: There are none in this email.\n\nBased on these key elements, I conclude that:\n\n* The sender\'s email address appears legitimate.\n* The subject line is generic and doesn\'t create a sense of urgency.\n* The email body contains information about Abakus and job listings without any social engineering tactics.\n* The hyperlinks provided lead to the official website of Abakus.\n\nGiven these factors, I believe that this email is likely **LEGITIMATE**.'}
    preprocessed_email = preprocess_email(parsed_email)
    response = get_email_score(preprocessed_email)
    return response