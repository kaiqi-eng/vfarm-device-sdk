from __future__ import annotations

from _common import make_client, unique_id


def main() -> None:
    farm_id = unique_id("sdk-example-farm")

    with make_client() as client:
        created = client.create_farm(
            farm_id=farm_id,
            name="SDK Example Farm",
            description="Created from farms_example.py",
            address="100 Example Way",
        )
        print("created:", created.model_dump())

        updated = client.update_farm(farm_id, address="200 Updated Rd")
        print("updated:", updated.model_dump())

        listed = client.list_farms(limit=10)
        print("listed_total:", listed.total)

        first_page_ids = [f.id for f in client.iter_farms(page_size=5)]
        print("iter_ids_sample:", first_page_ids[:5])

        inactive = client.deactivate_farm(farm_id)
        print("deactivated:", inactive.is_active)
        active = client.reactivate_farm(farm_id)
        print("reactivated:", active.is_active)

        client.delete_farm(farm_id)
        print("deleted:", farm_id)


if __name__ == "__main__":
    main()
