from faker import Faker
import random
import httpx
import asyncio
import math

faker = Faker()




types = ["Theft", "Fight", "Aggressive Person", "Drugs", "Strange Movement"]
base_location = [37.4219983, -122.084]

def generate_random_offset():
    """Gera um deslocamento aleatório para garantir uma distância entre 100 e 200 metros."""
    # Distância em graus (aproximadamente 0.0009 a 0.0018 graus)
    distance = random.uniform(0.0009, 0.0018)  

    # Direção aleatória em radianos
    angle = random.uniform(0, 2 * math.pi)

    # Cálculo do deslocamento usando seno e cosseno
    delta_lat = distance * math.cos(angle)
    delta_lng = distance * math.sin(angle) / math.cos(math.radians(base_location[0]))  # Ajuste para longitude

    return delta_lat, delta_lng

async def generate_occurrences():
    data = []

    for _ in range(20):
        delta_lat, delta_lng = generate_random_offset()
        new_lat = base_location[0] + delta_lat
        new_lng = base_location[1] + delta_lng

        data.append(
            {
                "description": faker.sentence(),
                "type": random.choice(types),
                "local": [new_lat, new_lng],
                "user_uuid": "b1709ce1-530c-422c-98b0-1c0c10963767"
            }
        )

    
    try:
        async with httpx.AsyncClient() as client:
            sended = 0
            for occurrence in data:
                sended += 1
                response = await client.post("http://localhost:8000/api/occurrences", json=occurrence)
                if response.status_code == 200:
                    print("Ocorrências enviadas com sucesso!")
                else:
                    print(f"Falha ao enviar ocorrências. Status code: {response.status_code} -> {response.text}")
    except httpx.RequestError as e:
        print(f"Ocorreu um erro ao tentar enviar as ocorrências: {e}")
        return False

async def main():
    await generate_occurrences()

if __name__ == "__main__":
    asyncio.run(main())