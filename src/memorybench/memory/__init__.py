"""Future memory integration boundary. Version 0 intentionally has no memory backend.

The runner constructs history before its first model request. A future retrieval policy
can add context at that boundary. Completed run events can feed a separate memory writer.
Keep retrieval, storage, and evaluation outside the tool execution loop.
"""
