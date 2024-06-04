import { Letter } from "react-letter";
import { extract } from "letterparser";

const EmailView = ({ email }: { email: string }) => {
  const { html, text, subject, from } = extract(email);

  return (
    <>
      <h2>Email Preview</h2>
      <div className="emailPreview">
        <h2 className="subjectText">{subject}</h2>
        <p className="fromText">
          {from?.name}
          {` <${from?.address}>`}
        </p>
        <Letter html={html} text={text} />
      </div>
    </>
  );
};

export default EmailView;
