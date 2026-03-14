import "../styles/login.css"
import { Link } from "react-router-dom"
import { Github, Mail, Lock, User } from "lucide-react"
import type { FormEvent } from "react"

function Signup() {

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    console.log("Signup form submitted")

    alert("Account created successfully! (Demo)")
  }

  return (
    <div className="login-wrapper">

      <div className="login-card">

        <h2>Create Your Account 🚀</h2>

        <p className="login-sub">
          Start your robotics journey with My Anybot
        </p>

        <form onSubmit={handleSubmit}>

          {/* NAME */}

          <div className="input-box">
            <User size={18}/>
            <input
              type="text"
              placeholder="Enter your full name"
              required
            />
          </div>


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
              type="password"
              placeholder="Create a password"
              required
              minLength={6}
            />
          </div>


          <button type="submit" className="login-btn">
            Create Account
          </button>

        </form>


        <div className="login-divider">
          <span></span>
          <p>or</p>
          <span></span>
        </div>


        <div className="social-buttons">

          <button type="button" className="social-btn">

            <img
              src="https://www.svgrepo.com/show/475656/google-color.svg"
              alt="Google"
              className="social-icon"
            />

            Sign up with Google

          </button>


          <button type="button" className="social-btn">

            <Github size={18}/>

            Sign up with GitHub

          </button>

        </div>


        <p className="create-account">
          Already have an account? <Link to="/login">Login</Link>
        </p>

      </div>

    </div>
  )
}

export default Signup