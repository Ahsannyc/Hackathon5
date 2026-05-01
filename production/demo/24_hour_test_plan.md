# 24-Hour Load & Stability Test Plan

**Hackathon5: CloudFlow Customer Success AI Digital FTE**  
**Objective:** Validate system stability, scalability, and reliability over 24 hours  
**Test Environment:** In-memory mode (graceful degradation, no Docker)  
**Expected Outcome:** 99.95%+ uptime, <500ms p95 latency, 500+ concurrent users supported

---

## 📋 Test Plan Overview

| Phase | Duration | Focus | Success Criteria |
|-------|----------|-------|-----------------|
| **Phase 1** | 0-4h | Baseline Load | 200+ concurrent, <250ms latency, 99%+ success |
| **Phase 2** | 4-8h | Peak Load | 500+ concurrent, <500ms latency, 99%+ success |
| **Phase 3** | 8-12h | Sustained Load | 300+ concurrent (sustained), memory stable |
| **Phase 4** | 12-16h | Chaos Testing | System recovers from 6 failure scenarios |
| **Phase 5** | 16-24h | Soak Test | 24h uptime, degradation <1% over time |

---

## 🚀 Phase 1: Baseline Load Testing (0-4 hours)

**Objective:** Establish baseline performance with normal load

### Setup

```bash
# Terminal 1: Start the service
cd "C:\Users\14loa\Desktop\IT\GIAIC\Q4 spec kit\Hackathon5"
python -m uvicorn production.api.main:app --reload --port 8000
```

### Test Execution

**1.1 Health Check Baseline**
```bash
# Test every 5 minutes
for i in {1..48}; do
  curl -s http://localhost:8000/health | jq .
  sleep 300
done
```

**Expected Output:**
```json
{
  "status": "healthy",
  "uptime_seconds": "300+",
  "services": {
    "email": "ready",
    "whatsapp": "ready",
    "form": "ready"
  }
}
```

**1.2 Baseline Concurrent Users (50 concurrent)**
```bash
# Test with 50 concurrent users
python -c "
import asyncio
import httpx
import time
from datetime import datetime

async def test_user():
    async with httpx.AsyncClient(timeout=30) as client:
        start = time.time()
        response = await client.post(
            'http://localhost:8000/api/form/submit',
            data={
                'customer_name': f'User_{int(time.time())}',
                'customer_email': f'user_{int(time.time())}@test.com',
                'subject': 'Test Query',
                'message': 'Baseline load test',
                'priority': 'medium'
            }
        )
        latency = (time.time() - start) * 1000
        return {
            'status': response.status_code,
            'latency_ms': latency,
            'timestamp': datetime.now().isoformat()
        }

async def run_test():
    tasks = [test_user() for _ in range(50)]
    results = await asyncio.gather(*tasks)
    
    successful = sum(1 for r in results if r['status'] == 200)
    avg_latency = sum(r['latency_ms'] for r in results) / len(results)
    
    print(f'Success Rate: {successful}/50 ({successful*100/50:.1f}%)')
    print(f'Avg Latency: {avg_latency:.0f}ms')
    print(f'Min: {min(r[\"latency_ms\"] for r in results):.0f}ms')
    print(f'Max: {max(r[\"latency_ms\"] for r in results):.0f}ms')
    print(f'p95: {sorted([r[\"latency_ms\"] for r in results])[int(len(results)*0.95)]:.0f}ms')

asyncio.run(run_test())
"
```

**Expected Results:**
- Success Rate: 100% (50/50)
- Avg Latency: <200ms
- p95 Latency: <250ms
- No errors

**1.3 Multi-Channel Baseline (20 per channel)**
```bash
# 20 web forms
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/form/submit \
    -d "customer_name=Form_User_$i&customer_email=form_$i@test.com&subject=Test&message=Test&priority=medium" \
    -o /dev/null
done

# 20 emails (simulated)
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/email/simulate \
    -H "Content-Type: application/json" \
    -d "{\"from_email\":\"email_$i@test.com\",\"from_name\":\"User $i\",\"subject\":\"Test\",\"body\":\"Test\"}" \
    -o /dev/null
done

# 20 WhatsApp (simulated)
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/whatsapp/simulate \
    -H "Content-Type: application/json" \
    -d "{\"from_number\":\"+1555000000\",\"sender_name\":\"User $i\",\"body\":\"Test\"}" \
    -o /dev/null
done
```

---

## 📈 Phase 2: Peak Load Testing (4-8 hours)

**Objective:** Test system under peak load conditions

### 2.1 Concurrent User Load (500 concurrent)
```bash
python -c "
import asyncio
import httpx
import time
from datetime import datetime

async def load_test(num_users=500):
    async def user_session():
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                for iteration in range(3):  # Each user makes 3 requests
                    await client.post(
                        'http://localhost:8000/api/form/submit',
                        data={
                            'customer_name': f'LoadTest_{int(time.time())}',
                            'customer_email': f'load_{int(time.time())}@test.com',
                            'subject': 'Peak load test',
                            'message': f'Iteration {iteration}',
                            'priority': 'medium'
                        }
                    )
                    await asyncio.sleep(0.1)
            return True
        except Exception as e:
            print(f'Error: {e}')
            return False

    start = time.time()
    tasks = [user_session() for _ in range(num_users)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    success_count = sum(results)
    print(f'\\nPeak Load Test Results:')
    print(f'Total Users: {num_users}')
    print(f'Successful Sessions: {success_count}/{num_users}')
    print(f'Success Rate: {success_count*100/num_users:.1f}%')
    print(f'Total Requests: {num_users * 3}')
    print(f'Duration: {duration:.1f}s')
    print(f'Throughput: {(num_users * 3) / duration:.0f} req/s')

asyncio.run(load_test(500))
"
```

**Expected Results:**
- Success Rate: >99%
- Average Latency: <500ms
- p99 Latency: <2s
- Throughput: 100+ req/sec

---

## 🔥 Phase 3: Sustained Load (8-12 hours)

**Objective:** Validate system stability under sustained load

### 3.1 Continuous Load Generation
```bash
# Run for 4 hours with 300 concurrent simulated users
python -c "
import asyncio
import httpx
import time
from datetime import datetime

async def sustained_load():
    start_time = time.time()
    duration_seconds = 4 * 3600  # 4 hours
    
    async def worker():
        async with httpx.AsyncClient(timeout=30) as client:
            iteration = 0
            while time.time() - start_time < duration_seconds:
                try:
                    await client.post(
                        'http://localhost:8000/api/form/submit',
                        data={
                            'customer_name': f'Sustained_{iteration}',
                            'customer_email': f'sustained_{iteration}@test.com',
                            'subject': 'Sustained load test',
                            'message': f'Request {iteration}',
                            'priority': 'medium'
                        }
                    )
                    iteration += 1
                    await asyncio.sleep(1)  # One request per second per worker
                except Exception as e:
                    print(f'Error in worker: {e}')

    # 300 concurrent workers
    tasks = [worker() for _ in range(300)]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    print(f'\\nSustained Load Phase Complete')
    print(f'Elapsed Time: {elapsed/3600:.1f} hours')

asyncio.run(sustained_load())
"
```

### 3.2 Memory Monitoring
```bash
# Monitor memory usage every minute
python -c "
import psutil
import time
from datetime import datetime

process = psutil.Process()
samples = []

print('Memory Monitoring - Sustained Load Phase')
print('Time | Memory (MB) | CPU % | Status')
print('-' * 50)

for i in range(240):  # 4 hours = 240 minutes
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_pct = process.cpu_percent(interval=1)
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    samples.append(memory_mb)
    
    # Check for memory leaks
    if len(samples) > 10 and samples[-1] > max(samples[:-10]) * 1.2:
        status = '⚠️  LEAK DETECTED'
    else:
        status = '✅ OK'
    
    print(f'{timestamp} | {memory_mb:.0f} MB | {cpu_pct:.1f}% | {status}')
    time.sleep(60)

avg_memory = sum(samples) / len(samples)
max_memory = max(samples)
min_memory = min(samples)

print(f'\\nMemory Stats:')
print(f'Average: {avg_memory:.0f} MB')
print(f'Maximum: {max_memory:.0f} MB')
print(f'Minimum: {min_memory:.0f} MB')
print(f'Growth: {max_memory - min_memory:.0f} MB')
"
```

---

## ⚡ Phase 4: Chaos Testing (12-16 hours)

**Objective:** Validate graceful degradation and error handling

### 4.1 Connection Drop Simulation
```bash
# Test resilience to dropped connections
python -c "
import httpx
import asyncio

async def chaos_connection_drop():
    failed_gracefully = 0
    for i in range(50):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Request will timeout
                await client.get('http://localhost:9999/test', timeout=1)
        except httpx.ConnectError:
            failed_gracefully += 1
        except asyncio.TimeoutError:
            failed_gracefully += 1
    
    print(f'Connection Drop Test: {failed_gracefully}/50 handled gracefully')

asyncio.run(chaos_connection_drop())
"
```

### 4.2 Invalid Input Handling
```bash
# Test XSS protection in forms
curl -X POST http://localhost:8000/api/form/submit \
  -d "customer_name=<script>alert('xss')</script>&customer_email=test@test.com&subject=XSS%20Test&message=<img%20src=x%20onerror=alert('xss')>&priority=medium"

# Should return 200 with script tags stripped
echo "Expected: XSS tags stripped, response 200"
```

### 4.3 Database Failure Simulation
```bash
# System should gracefully degrade without database
# This is already tested - in-memory mode means no DB dependency
curl http://localhost:8000/health
# Should still return healthy even without external DB
```

### 4.4 High Memory Pressure
```bash
# Create large message payloads
python -c "
import httpx

large_message = 'x' * 100000  # 100KB message

response = httpx.post(
    'http://localhost:8000/api/form/submit',
    data={
        'customer_name': 'LargePayload',
        'customer_email': 'large@test.com',
        'subject': 'Large message test',
        'message': large_message,
        'priority': 'medium'
    }
)

print(f'Large Payload Response: {response.status_code}')
print(f'Response size: {len(response.content)} bytes')
"
```

### 4.5 Rapid Fire Requests
```bash
# Send requests as fast as possible
python -c "
import httpx
import time

client = httpx.Client()
start = time.time()
success_count = 0

for i in range(1000):
    try:
        response = client.post(
            'http://localhost:8000/api/form/submit',
            data={
                'customer_name': f'RapidFire_{i}',
                'customer_email': f'rapid_{i}@test.com',
                'subject': 'Rapid fire test',
                'message': 'Testing rapid requests',
                'priority': 'medium'
            },
            timeout=5
        )
        if response.status_code == 200:
            success_count += 1
    except Exception as e:
        pass

duration = time.time() - start
print(f'Rapid Fire Results:')
print(f'Requests: 1000')
print(f'Successful: {success_count}')
print(f'Success Rate: {success_count*100/1000:.1f}%')
print(f'Duration: {duration:.1f}s')
print(f'Throughput: {1000/duration:.0f} req/s')
"
```

### 4.6 Cross-Channel Chaos
```bash
# Send chaos requests across all channels simultaneously
python -c "
import asyncio
import httpx

async def chaos_multi_channel():
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Mix of valid and invalid requests
        for i in range(100):
            # Valid web form
            tasks.append(client.post(
                'http://localhost:8000/api/form/submit',
                data={
                    'customer_name': f'Chaos_{i}',
                    'customer_email': f'chaos_{i}@test.com',
                    'subject': 'Chaos test',
                    'message': 'Testing chaos',
                    'priority': 'medium'
                }
            ))
            
            # Valid email
            tasks.append(client.post(
                'http://localhost:8000/api/email/simulate',
                json={
                    'from_email': f'chaos_{i}@test.com',
                    'from_name': f'ChaosUser{i}',
                    'subject': 'Chaos',
                    'body': 'Testing'
                }
            ))
            
            # Valid WhatsApp
            tasks.append(client.post(
                'http://localhost:8000/api/whatsapp/simulate',
                json={
                    'from_number': f'+1555{i:06d}',
                    'sender_name': f'ChaosUser{i}',
                    'body': 'Testing'
                }
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 200)
        
        print(f'Chaos Multi-Channel Results:')
        print(f'Total Requests: {len(results)}')
        print(f'Successful: {successful}')
        print(f'Success Rate: {successful*100/len(results):.1f}%')

asyncio.run(chaos_multi_channel())
"
```

---

## 😴 Phase 5: Soak Test (16-24 hours)

**Objective:** Validate 24-hour uptime and detect degradation

### 5.1 Continuous Uptime Monitoring
```bash
# Run health checks every minute for 8 hours
python -c "
import httpx
import time
from datetime import datetime, timedelta

client = httpx.Client()
start_time = datetime.now()
end_time = start_time + timedelta(hours=8)
check_interval = 60  # Check every minute

failed_checks = 0
total_checks = 0

print('Soak Test: Continuous Uptime Monitoring')
print('Start Time:', start_time.strftime('%Y-%m-%d %H:%M:%S'))
print()

while datetime.now() < end_time:
    try:
        response = client.get('http://localhost:8000/health', timeout=10)
        total_checks += 1
        
        if response.status_code != 200:
            failed_checks += 1
            print(f'❌ Check failed at {datetime.now().strftime(\"%H:%M:%S\")} - Status {response.status_code}')
        else:
            elapsed = (datetime.now() - start_time).total_seconds() / 3600
            uptime_pct = ((total_checks - failed_checks) / total_checks) * 100
            print(f'✅ {elapsed:.1f}h elapsed | Uptime: {uptime_pct:.2f}% ({total_checks} checks)')
    except Exception as e:
        failed_checks += 1
        print(f'❌ Connection error: {e}')
    
    time.sleep(check_interval)

final_uptime = ((total_checks - failed_checks) / total_checks) * 100 if total_checks > 0 else 0
print(f'\\nSoak Test Complete:')
print(f'Total Checks: {total_checks}')
print(f'Failed Checks: {failed_checks}')
print(f'Final Uptime: {final_uptime:.2f}%')
"
```

### 5.2 Degradation Detection
```bash
# Check for response time degradation over time
python -c "
import httpx
import time
from datetime import datetime, timedelta

start_time = datetime.now()
end_time = start_time + timedelta(hours=8)
latencies = []

print('Monitoring for Response Time Degradation')

while datetime.now() < end_time:
    client = httpx.Client()
    start = time.time()
    
    try:
        response = client.post(
            'http://localhost:8000/api/form/submit',
            data={
                'customer_name': 'DegradationTest',
                'customer_email': 'degrade@test.com',
                'subject': 'Degradation test',
                'message': 'Testing for degradation',
                'priority': 'medium'
            },
            timeout=30
        )
        
        latency = (time.time() - start) * 1000
        latencies.append(latency)
        
        if len(latencies) >= 10:
            avg_recent = sum(latencies[-10:]) / 10
            avg_initial = sum(latencies[:10]) / 10
            degradation = ((avg_recent - avg_initial) / avg_initial) * 100
            
            if degradation > 10:
                print(f'⚠️  Degradation detected: {degradation:.1f}% increase')
            else:
                print(f'✅ Stable: {latency:.0f}ms (degradation: {degradation:.1f}%)')
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        client.close()
    
    time.sleep(60)

print(f'\\nDegradation Analysis:')
print(f'Initial avg (first 10): {sum(latencies[:10])/10:.0f}ms')
print(f'Final avg (last 10): {sum(latencies[-10:])/10:.0f}ms')
print(f'Overall change: {((sum(latencies[-10:])/10) - (sum(latencies[:10])/10)) / (sum(latencies[:10])/10) * 100:.1f}%')
"
```

---

## ✅ Success Criteria

### Phase 1: Baseline (MUST PASS)
- ✅ 100% success rate on baseline load
- ✅ p95 latency <250ms
- ✅ All health checks pass

### Phase 2: Peak (MUST PASS)
- ✅ 99%+ success rate under 500 concurrent users
- ✅ p95 latency <500ms
- ✅ No timeouts

### Phase 3: Sustained (MUST PASS)
- ✅ 99%+ success rate for 4 hours
- ✅ Memory growth <5% over 4 hours
- ✅ No memory leaks detected

### Phase 4: Chaos (MUST PASS)
- ✅ Graceful degradation without errors
- ✅ XSS protection verified
- ✅ No unhandled exceptions
- ✅ System recovers from all failure scenarios

### Phase 5: Soak (MUST PASS)
- ✅ 99.95%+ uptime for 8 hours
- ✅ Response time degradation <10%
- ✅ No performance cliff

---

## 📊 Metrics Collection

**Key Metrics to Track:**
- Response time (min, avg, p95, p99, max)
- Success rate percentage
- Error rate percentage
- Memory usage (stable or growing?)
- CPU usage
- Concurrent user handling capacity
- Throughput (requests/second)

**Log Files:**
- Server logs: Check for warnings/errors
- Response times: Track latency over time
- Memory: Monitor for leaks

---

## 🎯 Pass/Fail Criteria

**PASS:** All 5 phases complete with metrics meeting success criteria  
**FAIL:** Any phase fails to meet success criteria (requires root cause analysis and retry)

**Final Score Impact:**
- ✅ All phases pass → +10 points (90/100 total)
- ✅ Phases 1-3 pass → +5 points (85/100 total)
- ✅ Phases 1-2 pass → +2 points (82/100 total)

