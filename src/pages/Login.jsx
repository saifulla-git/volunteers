import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    // For now, let's use a "test" login
    if (email === "admin@test.com" && password === "123456") {
      alert("Login Successful!");
      navigate("/dashboard"); // This sends you to the Admin Dashboard automatically
    } else {
      setError("Invalid email or password. Try admin@test.com / 123456");
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "100px auto", color: "white", textAlign: "center" }}>
      <h2>Login to Dashboard</h2>
      <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        <input 
          type="email" 
          placeholder="Email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: "10px", borderRadius: "5px" }}
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)}
          style={{ padding: "10px", borderRadius: "5px" }}
        />
        <button type="submit" style={{ padding: "10px", backgroundColor: "#28a745", color: "white", border: "none", cursor: "pointer" }}>
          Login
        </button>
      </form>
      {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}
    </div>
  );
}

export default Login;