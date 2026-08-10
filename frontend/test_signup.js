const axios = require('axios');
axios.post('http://localhost:8000/api/v1/auth/register', {
  email: "test2@example.com",
  password: "Password123!",
  name: "Test User"
}).then(res => console.log(res.data)).catch(err => {
  console.log("Error status:", err.response?.status);
  console.log("Error data:", JSON.stringify(err.response?.data, null, 2));
});
