const validatePassword = (pass) => {
    if (pass.length < 8) return "Password must be at least 8 characters long.";
    if (!/[A-Z]/.test(pass)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(pass)) return "Password must contain at least one lowercase letter.";
    if (!/\d/.test(pass)) return "Password must contain at least one number.";
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/.test(pass)) return "Password must contain at least one special character.";
    return "Accept";
  };

const tests = [
  "password123!",
  "PASSWORD123!",
  "Password!",
  "Password123",
  "Pass1!",
  "TripMate1!"
];

for (const t of tests) {
  console.log(`${t} -> ${validatePassword(t)}`);
}
