import { useEffect, useState } from "react";
import type { FileDropItem } from "react-aria";
import FileDropzone from "./FileDropzone";
import Results from "./Results";
import Loader from "./Loader";
import EmailView from "./EmailView";

export type Analysis = {
  phishing_score: number;
  reasons: string[];
  response: string;
};

const EmailAnalysis = () => {
  const [file, setFile] = useState<FileDropItem | File>();
  const [fileContents, setFileContents] = useState<string>();
  const [analysis, setAnalysis] = useState<Analysis>();
  const [error, setError] = useState<string>();

  // fake loading bar state
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!file) return;
    let cancelled = false;

    const contents = file instanceof File ? file.text() : file?.getText();
    contents.then((text) => {
      if (!cancelled) setFileContents(text);
    });
    return () => {
      setFileContents(undefined);
      cancelled = true;
    };
  }, [file]);

  useEffect(() => {
    if (!fileContents) return;
    let cancelled = false;

    fetch(`${import.meta.env.VITE_API_URL}/analyze-email`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: fileContents }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (!cancelled) setAnalysis(data);
      })
      .catch((error) => {
        if (!cancelled) setError(String(error));
      });

    return () => {
      setAnalysis(undefined);
      cancelled = true;
    };
  }, [fileContents]);

  if (!file)
    return (
      <>
        <h2>Upload an Email</h2>
        <FileDropzone setFile={setFile} />
      </>
    );

  if (error)
    return (
      <>
        <h2>Something went wrong</h2>
        {error}
      </>
    );

  if (!fileContents || !analysis || loading)
    return (
      <>
        <h2>Analyzing Email</h2>
        <Loader
          finished={!!analysis}
          onProgressFinished={() => {
            setLoading(false);
          }}
        />
        {fileContents && <EmailView email={fileContents} />}
      </>
    );

  return (
    <>
      <h2>Results</h2>
      <Results analysis={analysis} />
      <EmailView email={fileContents} />
    </>
  );
};

export default EmailAnalysis;
