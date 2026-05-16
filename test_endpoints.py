import httpx
import asyncio
import os

BASE_URL = "http://localhost:8000"

async def test_flow():
    print("Testing ScholARA End-to-End...")
    
    async with httpx.AsyncClient() as client:
        # 1. Register
        print("\n1. Registering user...")
        resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
            "full_name": "Test User"
        })
        if resp.status_code == 400 and "already registered" in resp.text:
            print("User already exists, proceeding to login.")
        try:
            resp.raise_for_status()
            print("Registration successful.")
        except Exception as e:
            if resp.status_code != 400:
                print(f"Error: {e}\nResponse: {resp.text}")
                return

        # 2. Login
        print("\n2. Logging in...")
        resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # 3. Upload Document
        print("\n3. Uploading document...")
        with open("dummy_paper.txt", "rb") as f:
            files = {"file": ("dummy_paper.txt", f, "text/plain")}
            resp = await client.post(f"{BASE_URL}/documents/upload", headers=headers, files=files)
            resp.raise_for_status()
            doc = resp.json()
            doc_id = doc["id"]
            print(f"Upload initiated. Document ID: {doc_id}")

        # 4. Wait for processing
        print("\n4. Waiting for document processing...")
        for _ in range(10):
            await asyncio.sleep(2)
            resp = await client.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
            status = resp.json()["status"]
            print(f"Status: {status}")
            if status == "ready":
                break
        else:
            print("Document processing timed out or failed.")
            return

        # 5. Create Chat Session
        print("\n5. Creating chat session...")
        resp = await client.post(f"{BASE_URL}/chat/sessions", headers=headers, json={"document_ids": [doc_id]})
        resp.raise_for_status()
        session_id = resp.json()["id"]
        print(f"Chat session created: {session_id}")

        # 6. Send Message (using streaming endpoint to test)
        print("\n6. Sending message...")
        async with client.stream("POST", f"{BASE_URL}/chat/stream", headers=headers, json={
            "session_id": session_id,
            "query": "What is the primary limitation of the study?",
            "document_ids": [doc_id]
        }) as response:
            print("Response stream:")
            async for chunk in response.aiter_text():
                print(chunk, end="", flush=True)
            print()
            
        # 7. Check Analytics
        print("\n7. Checking analytics...")
        resp = await client.get(f"{BASE_URL}/analytics/summary", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        print(f"Documents: {data['documents']['total']}")
        print(f"Sessions: {data['sessions']['total']}")
        print(f"Queries: {data['messages']['queries']}")
        print("\nAll tests passed successfully! [OK]")

if __name__ == "__main__":
    asyncio.run(test_flow())
