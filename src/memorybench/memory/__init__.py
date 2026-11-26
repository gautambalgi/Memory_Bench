"""Study Assistant memory and future integration points for the agent runner.

The V0 runner constructs history before its first model request. A future retrieval policy
can add context at that boundary. Completed run events can feed a separate memory writer.
Keep retrieval, storage, and evaluation outside the tool execution loop.
"""
