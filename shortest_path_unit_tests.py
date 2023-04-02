# PICK THE 2 CHARGE POINTS AT THE GIVEN COORDS AND FIND THE SHORTEST PATH

from classes import ChargeNetwork, ChargeStation
import pickle
import datetime
import visuals

with open('allnomin.pickle', 'rb') as file:
    obj = pickle.load(file)

set_of_chargers = obj.charge_stations()
for charger in set_of_chargers:
    if charger.coord == (44.977425, -64.920852):  # (39.292158, -120.678454):
        c1 = charger
    elif charger.coord == (41.500545, -95.451628): # (34.517047, -117.313614):
        c2 = charger

"""for charger in set_of_chargers:
    if (round(charger.coord[0]), round(charger.coord[1])) == (41, -121): # (39.292158, -120.678454):
        c1 = charger
    elif (round(charger.coord[0]), round(charger.coord[1])) == (40, -124): # (34.517047, -117.313614):
        c2 = charger
"""

print(f'start coord: {c1.coord}')
print(f'end coord: {c2.coord}')
result = obj.get_shortest_path(c1, c2)
print(f'total path length: {sum(edge.road_distance for edge in result)}km')

temp_graph = simplified_network = ChargeNetwork(-1, -1)
temp_graph._graph = {
    ChargeStation('', '', '', 0, 0, datetime.date(2000, 1, 1)): set(result)
}

all_chargers = set()
for edge in result:
    endpoints_iter = iter(edge.endpoints)
    p1 = next(endpoints_iter)
    if p1 not in all_chargers:
        all_chargers.add(p1)
    p2 = next(endpoints_iter)
    if p2 not in all_chargers:
        all_chargers.add(p2)

for charger in all_chargers:
    temp_graph.add_charge_station(charger, set())

visuals.graph_network(temp_graph)
