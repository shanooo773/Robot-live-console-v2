import { useState, useEffect } from "react";
import { useToast } from "@chakra-ui/react";
import { confirmEmail } from "../api";
import "../styles/verifyemail.css"; // 👈 ADD THIS

const VerifyEmailPage = ({ token, onSuccess }) => {
  const [status, setStatus] = useState("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const toast = useToast();

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMessage("No verification token found in the URL.");
      return;
    }

    confirmEmail(token)
      .then(() => {
        setStatus("success");
        toast({
          title: "Email verified!",
          description: "Your account is now active. You can sign in.",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      })
      .catch((error) => {
        setStatus("error");
        const detail =
          error.response?.data?.detail ||
          "This verification link is invalid or has expired.";
        setErrorMessage(detail);
      });
  }, [token, toast]);

  return (
    <div className="login-wrapper verify-wrapper">
      <div className="login-card" style={{ textAlign: "center" }}>

        {/* LOADING */}
        {status === "loading" && (
          <>
            <div className="verify-icon small">⏳</div>
            <h2 className="verify-title">Verifying Your Email...</h2>
            <p className="verify-sub">
              Please wait while we verify your account
            </p>
          </>
        )}

        {/* SUCCESS */}
        {status === "success" && (
          <>
            <div className="verify-icon">✅</div>
            <h2 className="verify-title">Email Verified!</h2>

            <p className="verify-sub">
              Your account has been activated. You can now sign in.
            </p>

            <button className="login-btn" onClick={onSuccess}>
              Go to Sign In
            </button>
          </>
        )}

        {/* ERROR */}
        {status === "error" && (
          <>
            <div className="verify-icon">❌</div>
            <h2 className="verify-title">Verification Failed</h2>

            <p className="verify-sub verify-error">
              {errorMessage}
            </p>

            <button className="login-btn" onClick={onSuccess}>
              Back to Sign In
            </button>
          </>
        )}

        <p className="secure-text">🔒 Your data is securely encrypted</p>

      </div>
    </div>
  );
};

export default VerifyEmailPage;