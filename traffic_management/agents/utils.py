def get_random_location() -> tuple[float, float]:
    """Generate a random location within a defined area."""
    import random

    x = round(random.uniform(0, 100), 3)
    y = round(random.uniform(0, 100), 3)
    return (x, y)


if __name__ == "__main__":
    location = get_random_location()
    print(f"Random location generated: {location}")
