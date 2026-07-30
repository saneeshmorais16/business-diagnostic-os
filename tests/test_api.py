def valid():return {"company_name":"Acme Ltd","industry":"technology","country":"UK","employees":50,"annual_revenue":1000000,"operating_cost":800000}
def test_health(client):assert client.get('/health').json()=={"status":"ok"}
def test_create_engagement(client):
    r=client.post('/api/v1/engagements',json=valid());assert r.status_code==201 and r.json()["id"]
def test_invalid_industry(client):
    d=valid();d["industry"]="unknown";assert client.post('/api/v1/engagements',json=d).status_code==422
def test_negative_employees(client):
    d=valid();d["employees"]=-1;assert client.post('/api/v1/engagements',json=d).status_code==422
def test_list_pagination(client):
    for i in range(3):d=valid();d["company_name"]+=str(i);client.post('/api/v1/engagements',json=d)
    assert len(client.get('/api/v1/engagements?page_size=2').json())==2
def test_filter_industry(client):
    client.post('/api/v1/engagements',json=valid());assert len(client.get('/api/v1/engagements?industry=technology').json())==1
def test_invalid_sort(client):assert client.get('/api/v1/engagements?sort=nope').status_code==400
def test_not_found_structure(client):
    r=client.get('/api/v1/engagements/999');assert r.status_code==404 and "error" in r.json()
def test_delete_cascade(client):
    i=client.post('/api/v1/engagements',json=valid()).json()["id"];assert client.delete(f'/api/v1/engagements/{i}').status_code==204;assert client.get(f'/api/v1/engagements/{i}').status_code==404
def test_security_headers(client):assert client.get('/').headers['x-frame-options']=='DENY'
def test_demo_seed(client):assert client.post('/demo',follow_redirects=False).status_code==303
def test_dashboard_usable(client):
    r=client.post('/demo',follow_redirects=False);assert client.get(r.headers['location']).status_code==200
def test_reject_non_csv(client):
    client.post('/demo');r=client.post('/engagements/1/upload',data={'dataset_type':'financial'},files={'file':('bad.exe',b'x','application/octet-stream')});assert r.status_code==415
def test_accept_valid_csv(client):
    client.post('/demo');data=b'date,revenue,gross_profit,operating_cost,budget_revenue\n2025-01-01,100,40,90,110\n2025-02-01,110,44,95,115';r=client.post('/engagements/1/upload',data={'dataset_type':'financial'},files={'file':('ok.csv',data,'text/csv')},follow_redirects=False);assert r.status_code==303
