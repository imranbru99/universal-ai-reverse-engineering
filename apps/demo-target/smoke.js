const http = require("http");

http
  .get("http://127.0.0.1:3100/health", (res) => {
    if (res.statusCode !== 200) process.exit(1);
    console.log("demo-target smoke ok");
  })
  .on("error", () => {
    console.log("demo-target not running; skip");
  });
