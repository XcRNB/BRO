{
  "builds": [
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/verify",
      "dest": "api/verify.py"
    },
    {
      "src": "/heartbeat",
      "dest": "api/heartbeat.py"
    },
    {
      "src": "/",
      "dest": "api/verify.py"
    }
  ]
}
app = app
