import requests
import time
import statistics

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "seu_token_aqui"  # Obtenha um token de autenticação

def time_request(url, headers=None):
    """Mede o tempo de uma requisição HTTP"""
    start = time.time()
    response = requests.get(url, headers=headers)
    end = time.time()
    return {
        "time": (end - start) * 1000,  # Convert to ms
        "status": response.status_code,
        "cache_hit": "X-Cache-Status" in response.headers and response.headers["X-Cache-Status"] == "HIT"
    }

def run_performance_test(endpoint, iterations=5):
    """Testa a performance de um endpoint com e sem cache"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print(f"Testing endpoint: {endpoint}")
    
    # Primeira requisição (sempre cache miss)
    print("First request (always cache miss):")
    result = time_request(f"{BASE_URL}{endpoint}", headers)
    print(f"  Time: {result['time']:.2f}ms, Status: {result['status']}")
    
    # Requisições subsequentes (devem usar cache)
    print("\nSubsequent requests (should use cache):")
    times = []
    for i in range(iterations):
        result = time_request(f"{BASE_URL}{endpoint}", headers)
        times.append(result["time"])
        print(f"  Request {i+1}: {result['time']:.2f}ms, Status: {result['status']}")
    
    avg_time = statistics.mean(times)
    print(f"\nAverage time for cached requests: {avg_time:.2f}ms")
    
    # Teste sem cache (usando um parâmetro único para forçar cache miss)
    print("\nRequests without cache (forced miss):")
    no_cache_times = []
    for i in range(iterations):
        # Use timestamp para garantir que cada requisição é única
        unique_param = f"&_={int(time.time() * 1000)}"
        result = time_request(f"{BASE_URL}{endpoint}{unique_param}", headers)
        no_cache_times.append(result["time"])
        print(f"  Request {i+1}: {result['time']:.2f}ms, Status: {result['status']}")
    
    avg_no_cache = statistics.mean(no_cache_times)
    print(f"\nAverage time for non-cached requests: {avg_no_cache:.2f}ms")
    
    # Comparação
    if avg_time < avg_no_cache:
        improvement = ((avg_no_cache - avg_time) / avg_no_cache) * 100
        print(f"\nCache provides a {improvement:.2f}% performance improvement")
    else:
        print("\nWarning: Cache doesn't seem to improve performance!")

if __name__ == "__main__":
    endpoints = [
        "/production/?year=2022", 
        "/production/wine?year=2022",
        "/exports/?year=2022",
        "/imports/?year=2022"
    ]
    
    for endpoint in endpoints:
        run_performance_test(endpoint)
        print("\n" + "="*50 + "\n")
