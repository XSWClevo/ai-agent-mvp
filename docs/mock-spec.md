# Mock File Spec

Location: mocks/<task-id>.mock.json

Required fields:
- task_id
- title
- description
- inputs
- outputs
- cases
- notes

Example:
```
{
  "task_id": "notion-xxxx",
  "title": "short title",
  "description": "mock purpose and scope",
  "inputs": {
    "params": {},
    "body": {}
  },
  "outputs": {
    "status": 200,
    "body": {}
  },
  "cases": [
    {
      "name": "happy-path",
      "inputs": {},
      "expected": {}
    }
  ],
  "notes": "edge cases / exclusions"
}
```
