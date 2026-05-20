{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/verify",
      "dest": "api/index.py"
    },
    {
      "src": "/heartbeat",
      "dest": "api/index.py"
    },
    {
      "src": "/",
      "dest": "api/index.py"
    },
    {
      "src": "/ping",
      "dest": "api/index.py"
    }
  ]
}
