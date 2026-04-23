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

  const HeroPanel = () => (
    <div className="auth-hero">
      <div className="auth-hero__logo">🤖 Anybot</div>
      <div className="auth-hero__tagline">Build. Code. Simulate.<br /><span>Learn Robotics.</span></div>
      <p className="auth-hero__sub">Access real ROS + Gazebo development environments designed for STEM students and future robotics engineers.</p>
      <ul className="auth-hero__features">
        <li>TurtleBot Navigation</li>
        <li>Robot Arm Manipulation</li>
        <li>Real-Time Simulation</li>
        <li>Live Video Feedback</li>
      </ul>
    </div>
  )

  // SUCCESS SCREEN
  if (sent) {
    return (
      <div className="login-wrapper">
        <HeroPanel />
        <div className="auth-form-panel">
          <div className="login-card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📧</div>
            <h2>Check Your Email</h2>
            <p className="login-sub">
              If an account exists for <strong>{email}</strong>, you will receive a password reset link shortly.
            </p>
            <button className="login-btn" onClick={onBack}>← Back to Login</button>
            <p className="secure-text">🔒 Your data is securely encrypted</p>
          </div>
        </div>
      </div>
    )
  }

  // FORM
  return (
    <div className="login-wrapper">
      <HeroPanel />
      <div className="auth-form-panel">
        <div className="login-card">
          <div className="auth-badge">🔒 Password Recovery</div>
          <h2>Forgot Password?</h2>
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

            <p className="back-login" onClick={onBack}>← Back to Login</p>
          </form>

          <p className="secure-text">🔒 Your data is securely encrypted</p>
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordPage