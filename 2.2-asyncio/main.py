import asyncio

import aiohttp

from models import Session, init_db
from models import People

SWAPI_URL = 'https://swapi.dev/api/people/?format=json'

HOMEWORLDS_URL = 'https://swapi.dev/api/planets/?format=json'
FILMS_URL = 'https://swapi.dev/api/films/?format=json'
SPECIES_URL = 'https://swapi.dev/api/species/?format=json'
STARSHIPS_URL = 'https://swapi.dev/api/starships/?format=json'
VEHICLES_URL = 'https://swapi.dev/api/vehicles/?format=json'

HOMEWORLDS_NAMES = {}
FILMS_NAMES = {}
SPECIES_NAMES = {}
STARSHIPS_NAMES = {}
VEHICLES_NAMES = {}


async def get_swapi_object_json(url, session):
    print('GET', url)
    async with session.get(url) as response:
        return await response.json()


async def get_swapi_object_name(data) -> dict:
    if 'url' in data.keys():
        key = data['url'].split('/')[-2]
    else:
        key = '?'

    if 'name' in data.keys():
        name = data['name']
    elif 'title' in data.keys():
        name = data['title']
    else:
        return {}

    return {key: name}


async def get_swapi_people_model_json(data) -> dict:
    return {"id": int(data['url'].split('/')[-2]),
            "name": data['name'],
            "birth_year": data['birth_year'],
            "eye_color": data['eye_color'],
            "gender": data['gender'],
            "hair_color": data['hair_color'],
            "height": data['height'],
            "homeworld": HOMEWORLDS_NAMES[data['homeworld'].split('/')[-2]],
            "mass": data['mass'],
            "skin_color": data['skin_color'],
            "films": ','.join([FILMS_NAMES[item.split('/')[-2]] for item in data['films']]),
            "species": ','.join([SPECIES_NAMES[item.split('/')[-2]] for item in data['species']]),
            "starships": ','.join([STARSHIPS_NAMES[item.split('/')[-2]] for item in data['starships']]),
            "vehicles": ','.join([VEHICLES_NAMES[item.split('/')[-2]] for item in data['vehicles']])}


async def swapi_paste_to_db(data):
    async with Session() as session:
        people = [People(**await get_swapi_people_model_json(item)) for item in data]

        session.add_all(people)
        print('Commit', len(people), 'people')
        await session.commit()


async def load_swapi_objects(url, session, object_dict):
    swapi_objects_json = await get_swapi_object_json(url, session)
    dict_list = [await get_swapi_object_name(item) for item in swapi_objects_json['results']]
    for d in dict_list:
        object_dict.update(d)
    if swapi_objects_json['next'] is not None:
        await load_swapi_objects(swapi_objects_json['next'], session, object_dict)
    else:
        await session.close()


async def load_swapi_people(url, session):
    swapi_people_json = await get_swapi_object_json(url, session)
    asyncio.create_task(swapi_paste_to_db(swapi_people_json['results']))
    if swapi_people_json['next'] is not None:
        await load_swapi_people(swapi_people_json['next'], session)


async def load_swapi_dict(url, di):
    session = aiohttp.ClientSession()
    task = asyncio.create_task(load_swapi_objects(url, session, di))
    return task


async def main():
    await init_db()

    task_list = [await load_swapi_dict(HOMEWORLDS_URL, HOMEWORLDS_NAMES),
                 await load_swapi_dict(FILMS_URL, FILMS_NAMES),
                 await load_swapi_dict(SPECIES_URL, SPECIES_NAMES),
                 await load_swapi_dict(STARSHIPS_URL, STARSHIPS_NAMES),
                 await load_swapi_dict(VEHICLES_URL, VEHICLES_NAMES)]
    await asyncio.gather(*task_list)

    async with aiohttp.ClientSession() as session:
        await load_swapi_people(SWAPI_URL, session)
        task_to_await = asyncio.all_tasks() - {asyncio.current_task()}
        await asyncio.gather(*task_to_await)

if __name__ == '__main__':
    asyncio.run(main())
