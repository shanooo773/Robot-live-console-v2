import "../styles/login.css"
import "../styles/forgotpasword.css"
import { Mail } from "lucide-react"
import { useState } from "react"
import { forgotPassword } from "../api"
import { useToast } from "@chakra-ui/react"

const ForgotPasswordPage = ({ onBack }) => {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const toast = useToast()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      await forgotPassword(email)
      setSent(true)

      toast({
        title: "Reset email sent",
        description: "Check your inbox for password reset link",
        status: "success",
        duration: 5000,
        isClosable: true,
      })
    } catch (error) {
      console.error("Forgot password error:", error)

      toast({
        title: "Error",
        description:
          error.response?.data?.detail || "Could not send reset email",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  // ✅ SUCCESS SCREEN
  if (sent) {
    return (
      <div className="login-wrapper">
        <div className="login-card" style={{ textAlign: "center" }}>

          <h2>📧 Check Your Email</h2>

          <p className="login-sub">
            If an account exists for <strong>{email}</strong>, you will receive a password reset link shortly.
          </p>

          <button className="login-btn" onClick={onBack}>
            ← Back to Login
          </button>

        </div>
      </div>
    )
  }

  // ✅ FORM UI
  return (
    <div className="login-wrapper">

      <div className="login-card">

        <h2>Forgot Password 🔒</h2>

        <p className="login-sub">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        <form onSubmit={handleSubmit}>

          <div className="input-box">
            <Mail size={18} />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              required
            />
          </div>

          <button className="login-btn" disabled={loading}>
            {loading ? "Sending..." : "Send Reset Link"}
          </button>

          {/* 🔥 Back button exactly below reset button */}
          <p className="back-login" onClick={onBack}>
            ← Back to Login
          </p>

        </form>

      </div>

    </div>
  )
}

export default ForgotPasswordPage