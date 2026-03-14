import "../styles/home.css"
import { Link } from "react-router-dom"
import { useSpring, animated, useTrail } from "@react-spring/web"
import { useState } from "react"
import {
Bot, Code2, Box, Hourglass, Cpu,
CalendarClock, Laptop, BoxSelect, Gamepad2,
ArrowRight, Menu, X
} from "lucide-react"

function Home() {

const [menuOpen,setMenuOpen] = useState(false)

const heroText = useSpring({
from: { opacity: 0, y: 60 },
to: { opacity: 1, y: 0 },
delay: 500,
config: { duration: 1200 }
})

const heroImage = useSpring({
from: { opacity: 0, x: 200 },
to: { opacity: 1, x: 0 },
delay: 500
})

const floatingRobot = useSpring({
from: { y: 0 },
to: async (next) => {
while (true) {
await next({ y: -10 })
await next({ y: 0 })
}
},
config: { duration: 4000 }
})

const features = [
{
icon: <Code2 size={22}/>,
title: "Smart Code Workspace",
desc: "Cloud-based ROS2 IDE with autocomplete and pre-configured libraries."
},
{
icon: <Box size={22}/>,
title: "Gazebo 3D Simulation",
desc: "Run realistic physics simulations with live sensors."
},
{
icon: <Hourglass size={22}/>,
title: "Reserved Dev Sessions",
desc: "Book dedicated cloud sessions with isolated resources."
},
{
icon: <Cpu size={22}/>,
title: "Multi-Robot Control",
desc: "Switch between TurtleBot, robotic arms and manipulators."
}
]

const trail = useTrail(features.length,{
from:{ opacity:0, y:80 },
to:{ opacity:1, y:0 },
delay:900
})

return (
<div className="page">

{/* NAVBAR */}
<div className="navbar">

<div className="nav-left">
<div className="logo-wrapper">
<Bot size={18}/>
</div>
<span className="logo-text">My Anybot</span>
</div>

{/* MOBILE MENU ICON */}
<div className="mobile-menu-icon">
{menuOpen
? <X size={26} onClick={()=>setMenuOpen(false)}/>
: <Menu size={26} onClick={()=>setMenuOpen(true)}/>
}
</div>

<div className={`nav-right ${menuOpen ? "open" : ""}`}>

<div className="nav-links">
<a href="#hero" onClick={()=>setMenuOpen(false)}>About</a>
<a href="#console" onClick={()=>setMenuOpen(false)}>Console</a>
<a href="#features" onClick={()=>setMenuOpen(false)}>Features</a>
<a href="#faq" onClick={()=>setMenuOpen(false)}>FAQ</a>
<a href="#contact" onClick={()=>setMenuOpen(false)}>Contact</a>

<Link to="/login" onClick={()=>setMenuOpen(false)}>
Login
</Link>
</div>

<Link to="/signup" className="btn-primary1">
Sign Up
</Link>

</div>
</div>


{/* HERO */}
<div id="hero" className="hero-split">

<animated.div
className="hero-content"
style={{
opacity: heroText.opacity,
transform: heroText.y.to(y => `translateY(${y}px)`)
}}
>

<h1>
Learn Robotics by
<br/>
Building Real Robots
</h1>

<p>
Hands-on platform for coding, simulating,
and controlling real robots.
</p>

<div className="hero-buttons">

<Link to="/signup">
  <button className="hero-primary-btn">
    Start Robotics
  </button>
</Link>

<a href="#console">
  <button className="hero-secondary-btn">
    Explore Platform
  </button>
</a>

</div>

</animated.div>


<animated.div
className="hero-image"
style={{
opacity: heroImage.opacity,
transform: heroImage.x.to(x => `translateX(${x}px)`)
}}
>

<animated.img
src="/pic1.png"
alt="Robotics Student"
style={{
transform: floatingRobot.y.to(y => `translateY(${y}px)`)
}}
/>

</animated.div>

</div>


{/* CONSOLE */}
<div id="console" className="console-section">

<h2>Powerful Cloud Robotics Console</h2>
<p>All-in-one platform for robotics development</p>

<div className="feature-grid">

{trail.map((style,index)=>(

<animated.div
key={index}
className="feature-card"
style={{
opacity: style.opacity,
transform: style.y.to(y => `translateY(${y}px)`)
}}
>

<div className="icon-box">
{features[index].icon}
</div>

<h3>{features[index].title}</h3>

<div className="divider"></div>

<p>{features[index].desc}</p>

</animated.div>

))}

</div>

<div className="big-cta-wrapper">
  <Link to="/login">
    <button className="big-cta-btn">
      Get Started
    </button>
  </Link>
</div>

</div>


{/* ENVIRONMENT */}
<div id="environment" className="environment-section">

<h2>Dedicated Development Environments</h2>
<p>Book your lab time & access isolated robotics resources on-demand.</p>

<div className="env-flow">

<div className="env-card">
<div className="env-icon">
<CalendarClock size={20}/>
</div>
<h3>Reserve Your Session</h3>
<p>Schedule dedicated lab time.</p>
</div>

<ArrowRight className="flow-arrow" size={20}/>

<div className="env-card">
<div className="env-icon">
<Laptop size={20}/>
</div>
<h3>Launch Workspace</h3>
<p>Access ROS2 environment.</p>
</div>

<ArrowRight className="flow-arrow" size={20}/>

<div className="env-card">
<div className="env-icon">
<BoxSelect size={20}/>
</div>
<h3>Simulate in Gazebo</h3>
<p>Run realistic 3D simulations.</p>
</div>

<ArrowRight className="flow-arrow" size={20}/>

<div className="env-card">
<div className="env-icon">
<Gamepad2 size={20}/>
</div>
<h3>Control Real Robots</h3>
<p>Deploy code to robots.</p>
</div>

</div>

</div>


{/* FEATURES */}
<div id="features" className="why-section">

<h2>Why Choose Anybot?</h2>
<p>Designed for modern robotics education & real-world simulation.</p>

<div className="why-grid">

<div className="why-card">
<div className="why-icon">
<Laptop size={24}/>
</div>
<h3>No Installation Required</h3>
<p>Everything runs in the cloud.</p>
</div>

<div className="why-card">
<div className="why-icon">
<BoxSelect size={24}/>
</div>
<h3>Real Hardware Integration</h3>
<p>Simulate in Gazebo and deploy to real robots.</p>
</div>

<div className="why-card">
<div className="why-icon">
<Cpu size={24}/>
</div>
<h3>Beginner to Advanced</h3>
<p>Perfect for students and robotics engineers.</p>
</div>

</div>

</div>


{/* FEEDBACK */}
<div className="feedback-section">

<h2>Feedback From Clients</h2>
<p>What educators and robotics professionals say about Anybot.</p>

<div className="feedback-slider">
<div className="feedback-track">

<div className="feedback-card">
<div className="client-image">
<img src="/saif.jpeg"/>
</div>
<p>The platform provides a smooth environment for coding, simulation, & real robot interaction, making
robotics learning practical & engaging for students.</p>
<h4>M. Saifullah Saeed</h4>
</div>

<div className="feedback-card">
<div className="client-image">
<img src="/tabarak.jpeg"/>
</div>
<p>Highly recommended for universities.The cloud-based simulation
and real robot control make it extremely useful for modern robotics</p>
<h4>Tabarak Rehman Chaudhary</h4>
</div>

<div className="feedback-card">
<div className="client-image">
<img src="/shahzaib.jpeg"/>
</div>
<p>Anybot is an impressive robotics platform. The cloud-based simulation and real robot control make it extremely useful for modern robotics education.</p>
<h4>Shahzaib</h4>
</div>

<div className="feedback-card">
<div className="client-image">
<img src="/haseeb.jpeg"/>
</div>
<p>The platform provides a smooth experience for learning robotics. Simulation tools and coding workspace are powerful and easy to use.</p>
<h4>Haseeb Shaukat</h4>
<span>CEO Terabit IT</span>
</div>

<div className="feedback-card">
<div className="client-image">
<img src="/laiq.jpeg"/>
</div>
<p>Anybot simplifies robotics learning by combining simulation, development, and real robot deployment in one place.</p>
<h4>Muhammad Bin Laiq</h4>
</div>

</div>
</div>

</div>


{/* FAQ */}
<div id="faq" className="faq-section">

<h2>Frequently Asked Questions</h2>
<p>Have questions? We'd love to hear from you.</p>

<div className="faq-container">

<details className="faq-item">
<summary>Do I need to install anything?</summary>
<p>No. Everything runs directly in your browser.</p>
</details>

<details className="faq-item">
<summary>Can I control real robots?</summary>
<p>Yes, after simulation you can deploy to real robots.</p>
</details>

<details className="faq-item">
<summary>Is Anybot beginner friendly?</summary>
<p>Yes, students and educators can easily use the platform.</p>
</details>

<details className="faq-item">
<summary>What technologies does Anybot use?</summary>
<p>ROS2, Gazebo simulation and cloud robotics environments.</p>
</details>

<details className="faq-item">
<summary>Can universities use this for labs?</summary>
<p>Yes, universities can schedule dedicated lab sessions.</p>
</details>

</div>

</div>


{/* CONTACT */}
<div id="contact" className="contact-section">

<h2>Get In Touch</h2>
<p>Have questions? We'd love to hear from you.</p>

<div className="contact-form">
<input type="text" placeholder="Your Name"/>
<input type="email" placeholder="Your Email"/>
<textarea placeholder="Your Message"/>
<button className="contact-btn">
Send Message
</button>
</div>

</div>


{/* FOOTER */}
<footer className="footer">

<div>© 2026 My Anybot</div>

<div className="footer-links">
<span>About</span>
<span>FAQ</span>
<span>Privacy</span>
<span>Contact</span>
</div>

</footer>

</div>
)
}

export default Home