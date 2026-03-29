import { useState } from "react";

function Home() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleJoin = async () => {
    if (!name || !email) {
      setMessage("Please fill in both fields.");
      return;
    }

    setIsSubmitting(true);
    setMessage("Connecting to backend...");

    try {
      const response = await fetch("/api/index", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage("✅ Success! You are registered.");
        setName("");
        setEmail("");
      } else {
        setMessage(`❌ Error: ${data.error || "Server failed"}`);
      }
    } catch (error) {
      setMessage("❌ Network Error: Could not reach the server.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "50px", color: "white" }}>
      <h1>Volunteer Registration</h1>
      <div style={{ display: "flex", justifyContent: "center", gap: "10px", marginTop: "20px" }}>
        <input
          type="text"
          placeholder="Your Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: "10px", borderRadius: "5px", border: "none" }}
        />
        <input
          type="email"
          placeholder="Your Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ padding: "10px", borderRadius: "5px", border: "none" }}
        />
        <button 
          onClick={handleJoin} 
          disabled={isSubmitting}
          style={{ 
            padding: "10px 20px", 
            borderRadius: "5px", 
            backgroundColor: isSubmitting ? "#555" : "#007bff", 
            color: "white", 
            border: "none",
            cursor: isSubmitting ? "not-allowed" : "pointer"
          }}
        >
          {isSubmitting ? "Joining..." : "Join Now"}
        </button>
      </div>
      <p style={{ marginTop: "20px" }}>{message}</p>
    </div>
  );
}

export default Home;