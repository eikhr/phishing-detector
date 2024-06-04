import { useEffect, useState } from "react";
import { ProgressBar, Label } from "react-aria-components";

type Props = {
  finished: boolean;
  onProgressFinished: () => void;
};

const Loader = ({ finished, onProgressFinished }: Props) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let interval;
    if (!finished) {
      interval = setInterval(() => {
        setProgress((prev) => prev + (100 - prev) * 0.001);
      }, 30);
    } else {
      interval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 1, 100));
      }, 30);
    }
    return () => clearInterval(interval);
  }, [finished]);

  useEffect(() => {
    if (progress === 100) {
      onProgressFinished();
    }
  }, [progress]);

  return (
    <div className="loaderContainer">
      <ProgressBar value={progress}>
        {({ percentage, valueText }) => (
          <>
            <Label>Analyzing...</Label>
            <span className="loadingBarValue">{valueText}</span>
            <div className="loadingBar">
              <div
                className="loadingBarFill"
                style={{ width: percentage + "%" }}
              />
            </div>
          </>
        )}
      </ProgressBar>
    </div>
  );
};

export default Loader;
