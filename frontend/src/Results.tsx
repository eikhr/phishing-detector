import { Heading, Label, ProgressBar } from "react-aria-components";
import { Analysis } from "./EmailAnalysis";
import { useEffect } from "react";

enum Verdict {
  Phishing,
  NotPhishing,
  Inconclusive,
}

const verdictText = {
  [Verdict.Phishing]: "likely phishing",
  [Verdict.NotPhishing]: "likely not phishing",
  [Verdict.Inconclusive]: "inconclusive",
};

const verdictColor = {
  [Verdict.Phishing]: "#cc0000",
  [Verdict.NotPhishing]: "#006600",
  [Verdict.Inconclusive]: "#ffc107",
};

const Results = ({ analysis }: { analysis: Analysis }) => {
  const verdict =
    analysis.phishing_score > 0.7
      ? Verdict.Phishing
      : analysis.phishing_score < 0.3
        ? Verdict.NotPhishing
        : Verdict.Inconclusive;

  useEffect(() => {
    document.body.style.backgroundColor = verdictColor[verdict];
  }, [verdict]);

  return (
    <div className="results">
      <div className="resultsTitleContainer">
        <h3>The email is {verdictText[verdict]}</h3>
        <ProgressBar value={analysis.phishing_score * 100}>
          {({ percentage, valueText }) => (
            <>
              <Label>Likelyhood of phishing</Label>
              <span className="phishingScoreValue">{valueText}</span>
              <div className="phishingScore">
                <div
                  className="phishingScoreFill"
                  style={{
                    width: percentage + "%",
                    backgroundColor: verdictColor[verdict],
                  }}
                />
              </div>
            </>
          )}
        </ProgressBar>
      </div>
      <ul className="reasonList">
        {analysis.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </div>
  );
};

export default Results;
