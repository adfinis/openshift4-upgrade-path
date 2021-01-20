#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# openshift4-upgrade-path - Compute shortest upgrade paths between OpenShift 4 releases.
#
# Copyright (C) 2020 Adfinis SyGroup AG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: 2020 Adfinis SyGroup AG
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import urllib.parse
import urllib.request
import json
import argparse


def channels(old, new, fast=False, candidate=False):
    # Generate all upgrade channel paths between the old and new version
    oldminor = int(old.split('.')[1])
    newminor = int(new.split('.')[1])
    clist = [f'stable-4.{i}' for i in range(oldminor, newminor+1)]
    if fast:
        clist += [f'fast-4.{i}' for i in range(oldminor, newminor+1)]
    if candidate:
        clist += [f'candidate-4.{i}' for i in range(oldminor, newminor+1)]
    return clist


def fetch_channel_graph(channel, arch='amd64'):
    query = urllib.parse.urlencode({
        'channel': channel,
        'arch': arch
    })
    url = f'https://api.openshift.com/api/upgrades_info/v1/graph?{query}'
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as response:
        channel_data = json.loads(response.read().decode())
    # Transform the upgrade path graph into adjacency list form
    edges = {}
    target_nodes = set()
    for edge in channel_data['edges']:
        outnode = channel_data['nodes'][edge[0]]['version']
        innode = channel_data['nodes'][edge[1]]['version']
        edges.setdefault(outnode, set()).add((innode, channel))
        target_nodes.add(innode)
    # Latest version is always the one with no outgoing edges
    latest = [k for k in target_nodes if k not in edges][0]
    return edges, latest


def merge_graphs_inplace(a, b):
    # Add all edges from the second graph to the first
    for k, v in b.items():
        a.setdefault(k, set()).update(v)


def dijkstra(edges, start, to):
    if to == start:
        # Nothing to do
        return []
    dist = {start: 0}
    nodes = set(edges.keys())
    path = {}
    while len(nodes) > 0:
        # Find next node to expand: min(dist[n] forall n in nodes)
        min_node = None
        for node in nodes:
            if node in dist:
                if min_node is None:
                    min_node = node
                elif dist[node] < dist[min_node]:
                    min_node = node
        if min_node is None:
            # No upgrade path
            break
        nodes.remove(min_node)
        # Expand all edges of min_node
        for edge, channel in edges.get(min_node, []):
            weight = dist[min_node] + 1
            # Update minimal node distance
            if edge not in dist or weight < dist[edge]:
                dist[edge] = weight
                # Save the full path for each
                path[edge] = path.get(min_node, []) + [(min_node, channel)]
    return path.get(to, None)


def main():
    ap = argparse.ArgumentParser(
        description='Compute a shortest upgrade path between two OpenShift 4 releases.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument('--fast',
                    action='store_true',
                    dest='fast',
                    help='Include the "fast-4.*" channels.')
    ap.add_argument('--candidate',
                    action='store_true',
                    dest='candidate',
                    help='Include the "candidate-4.*" channels.  This may produce unsupported upgrade paths and should not be used for production-grade clusters.')
    ap.add_argument('--arch', metavar='ARCH', type=str, dest='arch', default='amd64', help='The cluster CPU architecture.')
    ap.add_argument('current', metavar='CURRENT', type=str, help='The version to upgrade from.')
    ap.add_argument('target', metavar='TARGET', type=str, help='The version to upgrade to.')
    args = ap.parse_args()

    old_version = args.current
    new_version = args.target
    # Generate a list of upgrade channels
    clist = channels(old_version, new_version, fast=args.fast, candidate=args.candidate)

    # Fetch the upgrade path of each channel and merge the individual graphs into one
    graph = {}
    for channel in clist:
        subgraph, latest = fetch_channel_graph(channel, arch=args.arch)
        merge_graphs_inplace(graph, subgraph)
    # If only a "major.minor" version was passed, replace by the latest release for this version
    if len(new_version.split('.')) == 2:
        print(f'Using {latest} as target instead of {new_version}')
        new_version = latest
    # Find a shortest upgrade path
    path = dijkstra(graph, old_version, new_version)
    if path is None:
        print(f'No upgrade path from {old_version} to {new_version} found, using channels {", ".join(clist)}')
        exit(0)
    if len(path) == 0:
        print('No action required')
        exit(0)
    path.append((new_version, None))

    # Print the upgrade path
    print(f'Shortest Upgrade path from {old_version} to {new_version}:')
    for i in range(1, len(path)):
        oldversion = path[i-1][0]
        newversion = path[i][0]
        channel = path[i-1][1]
        print(f'  {oldversion} -> {newversion} using {channel}')


if __name__ == '__main__':
    main()
