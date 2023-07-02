import asyncio
import datetime

from aiohttp import ClientSession

from db_create import Session
from models import People

SWAPI_PEOPLE_URL = 'https://swapi.dev/api/people/'


async def get_page(url: str):
    """функция отправки запроса"""
    async with ClientSession() as s:
        async with s.get(url) as res:
            res = await res.json()
        await s.close()
    return res


async def get_detail_names(json: dict, detail: str, key: str):
    detail_requests = [get_page(url) for url in json[detail]]
    results = await asyncio.gather(*detail_requests)
    names = [res[key] for res in results]
    return ', '.join(names)


async def get_homeworld(json: dict):
    results = await get_page(json['homeworld'])
    return results['name']


async def main():
    session = Session()

    people_tasks = [asyncio.create_task(get_page(f'{SWAPI_PEOPLE_URL}{i}'))
                    for i in range(83)]

    people = await asyncio.gather(
        *people_tasks)  # выполняем подготовленный запрос

    for person in people:

        if person.get('detail') is None:
            detail_tasks = []

            films = asyncio.create_task(get_detail_names(person, 'films',
                                                         'title'))
            detail_tasks.append(films)  # подготовленные запросы

            homeworld = asyncio.create_task(get_homeworld(person))
            detail_tasks.append(homeworld)

            species = asyncio.create_task(get_detail_names(person,
                                                           'species', 'name'))
            detail_tasks.append(species)

            starships = asyncio.create_task(get_detail_names(person,
                                                             'starships',
                                                             'name'))
            detail_tasks.append(starships)

            vehicles = asyncio.create_task(get_detail_names(person,
                                                            'vehicles',
                                                            'name'))
            detail_tasks.append(vehicles)

            detail_res = await asyncio.gather(
                *detail_tasks)  # выполняем подготовленные запросы

            # создаем новый экземпляр класса People
            new_person = People(
                pers_id=int(person['url'].split('/')[-2]),
                birth_year=person['birth_year'],
                eye_color=person['eye_color'],
                films=detail_res[0],
                gender=person['gender'],
                hair_color=person['hair_color'],
                height=person['height'],
                homeworld=detail_res[1],
                mass=person['mass'],
                name=person['name'],
                skin_color=person['skin_color'],
                species=detail_res[2],
                starships=detail_res[3],
                vehicles=detail_res[4]
            )

            session.add(new_person)  # добавление данных в базу
            await session.commit()  # отправление данных в базу


if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(main())  # запуск кода
    print('Затраченное время', datetime.datetime.now() - start)
