import "../styles/login.css"
import { Link, useNavigate } from "react-router-dom"
import { Github, Mail, Lock, Eye, EyeOff } from "lucide-react"
import { useState } from "react"
import type { FormEvent } from "react"
import { useAppContext } from "../context/AppContext"

function Login() {

  const navigate = useNavigate()
  const { login } = useAppContext()

  const [loading,setLoading] = useState(false)
  const [showPassword,setShowPassword] = useState(false)

  const handleLogin = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    setLoading(true)

    setTimeout(()=>{
      login()
      navigate("/dashboard")
    },800)
  }

  return (

    <div className="login-wrapper">

      <div className="login-card">

        {/* LOGO */}
        <div className="login-logo">
          🤖 My Anybot
        </div>

        <h2>
          Welcome Back <span className="robot">🤖</span>
        </h2>

        <p className="login-sub">
          Login to continue to your robotics console
        </p>

        <form onSubmit={handleLogin}>

          {/* EMAIL */}

          <div className="input-box">

            <Mail size={18}/>

            <input
              type="email"
              placeholder="Enter your email"
              required
            />

          </div>


          {/* PASSWORD */}

          <div className="input-box">

            <Lock size={18}/>

            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              required
              minLength={6}
            />

            <button
              type="button"
              className="eye-btn"
              onClick={()=>setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
            </button>

          </div>


          {/* FORGOT PASSWORD */}

          <p className="forgot-pass">
            <Link to="/forgot">Forgot password?</Link>
          </p>


          {/* LOGIN BUTTON */}

          <button
            className="login-btn"
            disabled={loading}
          >
            {loading ? "Signing In..." : "Continue to Robotics Console"}
          </button>

        </form>


        {/* DIVIDER */}

        <div className="login-divider">
          <span></span>
          <p>or</p>
          <span></span>
        </div>


        {/* SOCIAL LOGIN */}

        <div className="social-buttons">

          <button className="social-btn">

            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              className="social-icon"
              alt="google"
            />

            Continue with Google

          </button>


          <button className="social-btn">

            <Github size={18}/>

            Continue with GitHub

          </button>

        </div>


        {/* CREATE ACCOUNT */}

        <p className="create-account">
          New to Anybot? <Link to="/signup">Create Account</Link>
        </p>


        {/* SECURITY MESSAGE */}

        <p className="secure-text">
          🔒 Your data is securely encrypted
        </p>

      </div>

    </div>

  )
}

export default Login