import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        # signup
        print("Registering...")
        res = await client.post("http://localhost:8000/auth/register", json={"email": "testagent2@test.com", "username": "testagent2", "password": "password", "full_name": "Test User"})
        print("register:", res.status_code)
        
        # login
        print("Logging in...")
        res = await client.post("http://localhost:8000/auth/login", json={"email": "testagent2@test.com", "password": "password"})
        if res.status_code != 200:
            print("login failed:", res.text)
            return
            
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # upload
        print("Uploading document...")
        with open("dummy_paper.txt", "rb") as f:
            res = await client.post("http://localhost:8000/documents/upload", headers=headers, files={"file": ("dummy.txt", f, "text/plain")})
        
        if res.status_code != 201:
            print("upload failed:", res.text)
            return
            
        doc_id = res.json()["id"]
        print("upload doc_id:", doc_id)
        
        # wait for ingestion
        print("waiting for ingestion...")
        for i in range(15):
            await asyncio.sleep(2)
            doc_status = await client.get(f"http://localhost:8000/documents/", headers=headers)
            docs = doc_status.json()
            doc = next((d for d in docs if d["id"] == doc_id), None)
            if doc and doc["status"] == "ready":
                print(f"ingestion complete! {doc['chunk_count']} chunks created.")
                break
            elif doc and doc["status"] == "error":
                print(f"ingestion error: {doc['error_message']}")
                return
        
        # chat session
        print("Creating chat session...")
        res = await client.post("http://localhost:8000/chat/sessions", headers=headers, json={"title": "Test Chat", "document_ids": [doc_id]})
        session_id = res.json()["id"]
        
        # send message
        print("sending message to agent...")
        res = await client.post("http://localhost:8000/chat/message", headers=headers, json={"session_id": session_id, "query": "What is the main idea of this text?", "document_ids": [doc_id]}, timeout=60.0)
        
        if res.status_code != 200:
            print("Chat message failed:", res.text)
            return
            
        print("\n--- AGENT RESPONSE ---")
        print(json.dumps(res.json(), indent=2))

asyncio.run(test())
