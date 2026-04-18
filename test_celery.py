from app.tasks import test_task, slow_task

print("🚀 Отправляем тестовую задачу...")
result = test_task.delay()
print(f"Task ID: {result.id}")

# Ждём результат
task_result = result.get(timeout=10)
print(f"Результат: {task_result}")

print("\n🔄 Отправляем медленную задачу (3 секунды)...")
slow_result = slow_task.delay(3)
print(f"Slow Task ID: {slow_result.id}")
slow_task_result = slow_result.get(timeout=10)
print(f"Результат медленной задачи: {slow_task_result}")

print("\n✅ Все тесты Celery пройдены!")