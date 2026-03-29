import { useState } from 'react'
import './App.css'

function App() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('Sending...')
    
    // Now talking to your merged Vercel backend!
    try {
      const response = await fetch('/api/add-volunteer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email })
      })
      
      if (response.ok) {
        setStatus('Success! You are registered.')
        setName('')
        setEmail('')
      } else {
        setStatus('Error. Try again.')
      }
    } catch (err) {
      setStatus('Could not connect to the server.')
    }
  }

  return (
    <div className="App">
      <h1>Volunteer Registration</h1>
      <form onSubmit={handleSubmit}>
        <input 
          type="text" 
          placeholder="Your Name" 
          value={name}
          onChange={(e) => setName(e.target.value)} 
          required 
        />
        <input 
          type="email" 
          placeholder="Your Email" 
          value={email}
          onChange={(e) => setEmail(e.target.value)} 
          required 
        />
        <button type="submit">Join Now</button>
      </form>
      <p>{status}</p>
    </div>
  )
}

export default App