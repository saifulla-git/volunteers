import { useEffect, useState } from "react";

export default function Dashboard() {
  const [list, setList] = useState([]);

  useEffect(() => {
    fetch("/api/volunteers") // We need to add this 'GET' route to your Python file next!
      .then(res => res.json())
      .then(data => setList(data))
      .catch(err => console.log("Fetch error:", err));
  }, []);

  return (
    <div>
      <h1>Volunteer Database</h1>
      <table border="1" style={{ width: "100%", textAlign: "left", color: "white" }}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          {list.map((person, i) => (
            <tr key={i}>
              <td>{person.name}</td>
              <td>{person.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}