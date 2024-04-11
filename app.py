from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from bab import BacABank


app = FastAPI()
bacabank = BacABank()
class LoginDetails(BaseModel):
    username: str
    password: str
    account_number: str
@app.post('/login', tags=["login"])
def login_api(input: LoginDetails):
        
        session_raw = bacabank.login(input.username, input.password)
        return session_raw

@app.post('/get_balance', tags=["get_balance"])
def get_balance_api(input: LoginDetails):
        session_raw = bacabank.login(input.username, input.password)
        balance = bacabank.get_balance()
        return balance
class Transactions(BaseModel):
    username: str
    password: str
    account_number: str
    limit: int
    from_date: str
    to_date: str
    
@app.post('/get_transactions', tags=["get_transactions"])
def get_transactions_api(input: Transactions):
        session_raw = bacabank.login(input.username, input.password)
        history = bacabank.get_transactions(input.from_date,input.to_date,input.limit)
        return history
if __name__ == "__main__":
    uvicorn.run(app ,host='0.0.0.0', port=3000)