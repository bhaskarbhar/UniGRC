import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Login attempted for ${email}`);
  };

  return (
    <div className="login-container">
      <div className="login-box">
        {/* <img src="/logo.svg" alt="Logo" className="logo" /> */}
        <h2>Welcome back!</h2>
        <p className="subtext">Please enter your details to sign in.</p>

        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="email"
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="forgot-password">
            <Link to="/forgot">Forgot password?</Link>
          </div>
          <button type="submit">Sign in</button>
        </form>

        <p className="signup-link">
          Not a member? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
