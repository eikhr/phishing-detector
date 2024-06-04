import banner from "/banner.webp";
import EmailAnalysis from "./EmailAnalysis.tsx";

function App() {
  return (
    <div className="container">
      <img
        src={banner}
        className="banner"
        alt="Phishing detection illustration"
      />
      <h1>Phishing Email Detector</h1>
      <div className="mainContent">
        <EmailAnalysis />
      </div>
    </div>
  );
}

export default App;
