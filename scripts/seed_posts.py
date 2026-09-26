"""
Seed the database with test posts and ground truth evaluation set.

Creates ~15 blog posts with realistic content and links them to
images via the EvalSet table for evaluation.

Usage:
    python scripts/seed_posts.py
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.database import Post, EvalSet
from app.jobs.embedding_batch import generate_embedding
from app.core.cost_tracker import log_gemini_call
import random


TEST_POSTS = [
    {
        "title": "The Mysterious Red Fox",
        "content": """The red fox is one of nature's most adaptable predators. These clever canines
have successfully colonized landscapes across the Northern Hemisphere, from arctic tundra to
temperate forests. Their distinctive orange-red fur, white-tipped tails, and black ear tips make
them easily recognizable. Red foxes are nocturnal hunters, preying on small rodents, rabbits,
and insects. Their intelligence and problem-solving abilities have earned them a place in
folklore and mythology across many cultures.""",
        "keywords": ["fox", "predator", "canine", "hunting"],
    },
    {
        "title": "Wolves: Nature's Top Predators",
        "content": """Wolves are apex predators that play a crucial role in maintaining ecological
balance. Living in highly organized pack structures, wolves hunt cooperatively using sophisticated
communication and strategy. These magnificent animals can travel up to 40 miles per day in search
of food. Their haunting howls serve as territorial markers and help coordinate pack activities.
Despite their fearsome reputation, wolves are generally shy around humans and attacks are extremely rare.""",
        "keywords": ["wolf", "predator", "pack", "hunting"],
    },
    {
        "title": "Graceful Deer in Natural Habitats",
        "content": """Deer are elegant herbivores found across most of the Northern Hemisphere. These
graceful animals are perfectly adapted to forest and grassland environments. Male deer, called bucks,
grow impressive antlers each year which they shed and regrow. Deer communicate through a variety of
vocalizations and body language. Their population dynamics have significant impacts on forest ecology
through browsing patterns. Observing deer in their natural habitat is a favorite pastime for wildlife enthusiasts.""",
        "keywords": ["deer", "herbivore", "antlers", "forest"],
    },
    {
        "title": "Bears: Powerful Omnivores",
        "content": """Bears are among the largest land carnivores, though they are actually omnivorous.
These powerful animals possess incredible strength and intelligence. Different bear species have adapted
to diverse habitats from arctic regions to temperate forests. Bears are solitary creatures except during
mating season and when mothers raise their cubs. Their diet varies seasonally, with some bears consuming
salmon during spawning runs. Conservation efforts are crucial for protecting these magnificent animals.""",
        "keywords": ["bear", "omnivore", "predator", "forest"],
    },
    {
        "title": "Eagles: Masters of the Sky",
        "content": """Eagles are majestic raptors that command the skies with incredible prowess. These
powerful birds of prey have exceptional vision, able to spot prey from miles away. Eagles are known for
their dramatic courtship displays and strong pair bonds. They build enormous nests called eyries on high cliff
faces and tall trees. Different eagle species have adapted to various prey preferences, from fish to small mammals.
The bald eagle has become a symbol of freedom and power across North America.""",
        "keywords": ["eagle", "bird", "predator", "raptor"],
    },
    {
        "title": "Forest Ecosystems and Biodiversity",
        "content": """Forests are among the most biodiverse ecosystems on Earth, supporting countless species of
plants, animals, and microorganisms. The forest canopy creates multiple distinct layers, each with unique environmental
conditions and inhabitants. Trees provide food, shelter, and breeding grounds for wildlife while also producing oxygen
and storing carbon. Forest ecosystems play a vital role in regulating global climate patterns and water cycles.
Deforestation threatens these delicate systems and the many species that depend on them.""",
        "keywords": ["forest", "tree", "ecosystem", "biodiversity"],
    },
    {
        "title": "Mountain Landscapes and Wildlife",
        "content": """Mountains present harsh but fascinating environments where specialized wildlife thrives. The altitude
creates distinct climate zones, each supporting different plant and animal communities. Mountain ecosystems face unique
challenges from erosion, avalanches, and extreme weather conditions. Many species have evolved remarkable adaptations
to survive in these high-altitude environments. Mountain ranges serve as important corridors for wildlife migration and
gene flow between populations.""",
        "keywords": ["mountain", "landscape", "altitude", "wildlife"],
    },
    {
        "title": "River Ecosystems and Aquatic Life",
        "content": """Rivers are dynamic ecosystems that support diverse communities of aquatic and terrestrial organisms.
The flowing water creates gradients of oxygen, temperature, and nutrient levels that support different species at different
locations. Fish migrate upstream to spawn, supporting both aquatic and terrestrial predators. Rivers also provide critical
habitat for amphibians, reptiles, and mammals that depend on the water. River health is essential for both wildlife and
human communities that depend on these vital waterways.""",
        "keywords": ["river", "water", "aquatic", "ecosystem"],
    },
    {
        "title": "Ocean Wonders and Marine Biodiversity",
        "content": """The ocean covers most of Earth's surface and contains incredible biodiversity. Marine ecosystems range
from shallow coral reefs to deep-sea trenches, each with unique communities of organisms. Whales, dolphins, and sharks are
just a few of the charismatic megafauna that inhabit our oceans. Plankton form the base of marine food webs, producing
much of the world's oxygen. Ocean health is critical for maintaining global climate stability and supporting human food security.""",
        "keywords": ["ocean", "marine", "sea", "biodiversity"],
    },
    {
        "title": "Predator-Prey Relationships in Nature",
        "content": """The interactions between predators and prey shape ecosystem dynamics and evolution. Predators help control
prey populations and remove weak or diseased individuals. This selection pressure drives prey species to evolve better defenses
and evasion strategies. Arms races between predators and prey lead to remarkable adaptations like camouflage, speed, and armor.
Understanding these relationships is crucial for conservation and ecosystem management. Disrupting predator-prey relationships can
have cascading effects throughout entire ecosystems.""",
        "keywords": ["predator", "prey", "hunting", "ecosystem"],
    },
    {
        "title": "Seasonal Migrations of Wildlife",
        "content": """Many animal species undertake remarkable migrations across vast distances in response to seasonal changes.
Birds migrate between breeding grounds in northern regions and wintering grounds in the south. Whales migrate thousands of miles
for feeding and breeding. Land mammals like wildebeest undertake epic migrations across African plains. These migrations require
enormous energy expenditure and navigation abilities. Climate change is disrupting traditional migration patterns with serious
consequences for many species.""",
        "keywords": ["migration", "seasonal", "movement", "wildlife"],
    },
    {
        "title": "Conservation Success Stories",
        "content": """Despite environmental challenges, there are inspiring examples of successful conservation efforts. Species
like the Arabian oryx and California condor have been brought back from the brink of extinction through dedicated conservation work.
Marine protected areas have helped rebuild fish populations. Habitat restoration projects have created corridors for wildlife movement.
These successes demonstrate that with commitment and resources, we can reverse some conservation losses. However, much more work
remains to protect endangered species and ecosystems.""",
        "keywords": ["conservation", "endangered", "protection", "species"],
    },
    {
        "title": "Adaptations: Evolution in Action",
        "content": """Animals display remarkable adaptations that demonstrate the power of evolution. Camouflage allows predators and
prey to hide from each other. Specialized beaks and claws allow different bird species to exploit different food sources. Thick fur
and fat layers insulate Arctic animals from extreme cold. Poison and venom deter predators and help animals subdue prey. These
adaptations took millions of years to evolve through natural selection. Understanding adaptations helps us appreciate the incredible
diversity of life on Earth.""",
        "keywords": ["adaptation", "evolution", "survival", "species"],
    },
    {
        "title": "Nocturnal Wildlife and Night Hunting",
        "content": """Many animals are active at night, taking advantage of darkness to hunt, forage, or avoid diurnal predators. Nocturnal
adaptations include large eyes, sensitive hearing, and enhanced smell to navigate in darkness. Many predators like owls and foxes hunt
under cover of darkness. Prey species have counter-evolved defenses like nocturnal activity patterns of their own. The night brings a
completely different cast of characters to ecosystems, from nocturnal insects to owls to bats. Understanding nocturnal wildlife requires
special observation techniques and night vision equipment.""",
        "keywords": ["nocturnal", "night", "hunting", "darkness"],
    },
    {
        "title": "Parental Care in the Animal Kingdom",
        "content": """Different animal species exhibit a wide range of parenting strategies. Mammals typically provide extended care to their
offspring, teaching them survival skills. Birds feed their chicks and protect them from predators. Some reptiles and fish provide no parental
care at all, relying on producing large numbers of offspring. Parental investment affects reproductive success and offspring survival rates.
The quality of parental care directly impacts population dynamics and species fitness. Evolution has shaped parenting strategies to match
each species' ecological niche and life history.""",
        "keywords": ["parental care", "offspring", "reproduction", "family"],
    },
]


def create_test_posts(db: Session) -> dict:
    """Create test posts with embeddings."""
    created_posts = []

    for post_data in TEST_POSTS:
        try:
            combined_text = f"{post_data['title']} {post_data['content']}"
            embedding = generate_embedding(combined_text)

            post = Post(
                title=post_data["title"],
                content=post_data["content"],
                embedding=embedding,
            )

            db.add(post)
            db.flush()

            log_gemini_call(
                db,
                call_type="embedding",
                model="text-embedding-004",
                cost_usd=0.00002,
                post_id=post.id,
                status="success",
            )

            created_posts.append({
                "id": post.id,
                "title": post.title,
                "keywords": post_data["keywords"],
            })

            print(f"✓ Created post: {post.title}")

        except Exception as e:
            print(f"✗ Failed to create post: {str(e)}")

    db.commit()
    return created_posts


def link_posts_to_images(db: Session, posts: dict):
    """
    Link posts to images via EvalSet.

    This creates ground truth mappings for evaluation.
    In a real scenario, you'd manually curate these mappings.
    """
    from app.models.database import Image

    images = db.query(Image).all()
    if not images:
        print("⚠️  No images found. Skipping EvalSet creation.")
        return

    eval_count = 0

    for post in posts[:min(10, len(posts))]:
        try:
            random_image = random.choice(images)

            existing = db.query(EvalSet).filter(EvalSet.post_id == post["id"]).first()
            if existing:
                continue

            eval_set = EvalSet(
                post_id=post["id"],
                correct_image_id=random_image.id,
            )

            db.add(eval_set)
            eval_count += 1
            print(f"✓ Linked post {post['id']} to image {random_image.id}")

        except Exception as e:
            print(f"✗ Failed to create eval mapping: {str(e)}")

    db.commit()
    return eval_count


def main():
    """Seed posts and evaluation set."""
    print("📝 FlyRank Post Seeding Pipeline")
    print("=" * 50)

    db = SessionLocal()
    try:
        print("\n🔍 Step 1: Create test blog posts")
        posts = create_test_posts(db)
        print(f"   Created {len(posts)} posts")

        print("\n🎯 Step 2: Link posts to images (ground truth)")
        eval_count = link_posts_to_images(db, posts)
        print(f"   Created {eval_count} eval set mappings")

        print(f"\n✅ Complete!")
        print(f"\n   View results:")
        print(f"   - GET http://localhost:8000/posts")
        print(f"   - GET http://localhost:8000/eval/precision")

    finally:
        db.close()


if __name__ == "__main__":
    main()
