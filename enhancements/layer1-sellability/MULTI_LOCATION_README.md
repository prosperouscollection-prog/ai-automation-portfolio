# Multi-Location Support

## Overview

`multi_location_router.py` upgrades any Genesis AI Systems lead workflow from single-site logic to location-aware routing. This is how you move from small-business pricing into multi-site and enterprise-style deals.

Commercial positioning:

- charge `2x` the base system price for each additional location

## What It Handles

- ZIP code routing
- caller area code routing
- keyword-based routing
- location-specific sheet tabs
- location-specific phone numbers and emails
- location-specific system prompt variations

## Routing Strategy

The default routing chain is:

1. ZIP code
2. area code
3. keyword
4. fallback to the default location

## Example Use Cases

- dental group with two offices and separate front desks
- HVAC company with territory-based dispatch zones
- salon owner with multiple storefronts

## Technical Notes

- maximum of 10 locations per client
- use `CompositeLocationRouter` when multiple strategies are needed
- keep the location config in a JSON file, database table, or n8n data store

## Upsell Positioning

This enhancement is best sold when the client says:

- "We have two locations."
- "Different zip codes go to different teams."
- "Our downtown office handles different services."
