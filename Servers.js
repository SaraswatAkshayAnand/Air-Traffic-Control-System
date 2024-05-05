const express = require('express');
const { PythonShell } = require('python-shell');
const app = express();
const port = 3000;

// Define routes
app.get('/', (req, res) => {
  // Run your Python tkinter script using PythonShell
  PythonShell.run('main.py', null, (err, results) => {
    if (err) throw err;
    console.log('Python script finished.');
    res.send('Python script finished.');
  });
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
