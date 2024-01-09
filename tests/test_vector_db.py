import json

import pytest

from overlore.db.handlerVec import VectorDatabaseHandler

input_list = [
    """
        Nancy: The fields whisper tales of our victory, but what worth is gold if our stomachs echo with emptiness?
        James: That's just it, isn't it? We've struck the earth till our hands bled, only to trade our fish for a pitiful sum of gold. Fools' math!
        Lisa: Let peace fill your hearts, friends. We grieve for the fallen, yet our defenses still stand. There is hope in our unity.
        Daniel: Hope? Speak not to me of hope when swords clash outside our doors. We must fortify, prepare! Besides, the mines won't shield us nor fill our plates.
        Paul: Our plows lay idle and our nets gather dust. What good is coin when the wheat does not sway and the fish leap away from our grasp?
        James: Rage swells within! What good is a war won when our own people lie dead? Tell me that, friends! Tell me!
        Nancy: Listen to the wind, for it carries both the songs of triumph and the cries of the hungry. Victory is a fickle mistress.
        Lisa: Peace, James. Let not anger cloud our judgment. The earth has riches yet to yield, and the seas will provide. We must toil together.
        Daniel: Toil, you say! It's time to wield the pickaxe as a spear if need be. Our brethren were not lost to toil, but to bloodshed.
        Paul: Aye, it's the toil that's forgotten once the blood dries. Perhaps the lesson here lies not in the clashing of swords but in the joining of hands.
        Nancy: With a bounty of gold and an ache in our bellies, we stand at a crossroads. Shall we eat or shall we arm? That is the question, and the crops won't wait.
    """,
    """
        Nancy: The barns are full, yet my heart is heavy with worry. Prosperity today doesn't guarantee safety tomorrow.
        James: Our nets overflow, but it's the empty stomachs of our fallen brethren that weigh on me. When will this cycle end?
        Lisa: Look around! Our granaries are stocked, and our defenses have never been stronger. We must take heart in our capabilities.
        Daniel: They say plenty brings peace, but I can't shake the feeling of impending doom. Our walls may be sturdy, but are our spirits?
        Paul: Laughter fills our taverns, and yet the price of such joy is never far from my thoughts. How many more must we lose for this comfort?
        Nancy: Let's not forget those who toil and those who have fallen. Our plenty is built on their sacrifices.
        Lisa: True strength lies not in walls or wealth but in the will to keep striving. We must honor the fallen by living fully.
        James: I hear your words, yet the anger inside me stirs like a tempest. We trade, we fight, but what are we truly gaining?
        Daniel: Let's use our abundance to fortify, not just in stone, but in spirit. Our next challenge may be just around the corner.
        Paul: Aye, we feast tonight, but tomorrow we must wake with the dawn and work as one. Our unity is our greatest treasure.
    """,
    """
        Nancy: Our granaries may be full, but my heart races with unease. Can joy truly bloom on such shaky ground?
        James: Riches in grain, yet here we stand behind crumbling walls. What's the worth of a full belly when danger lurks?
        Lisa: The fields yield more than ever, and yet, isn't it peace that truly nourishes the soul? Let's not forget our inner harmony.
        Daniel: Abundance surrounds us, but it's as if we're awaiting a storm. How do we prepare when our very foundations quiver?
        Paul: Feasts fill our days, but doubt clouds my nights. Are we merely fattening ourselves for a fall?
        Nancy: Hope guides me, yet worry taints it. We must find balance between enjoying our bounty and safeguarding our future.
        Lisa: Joy in abundance! Let's not dampen it with undue fear. For today, we have food, and tomorrow, we'll face together.
        James: My fury isn't quelled by wheat or gold. It's security I crave, and that, friends, is in short supply.
        Daniel: Alert and fed, yet what use is a vigilant watch when the enemy can breach at will? Our prosperity is precarious.
        Paul: We might laugh now, but skepticism keeps my mirth in check. Let's not be blinded by our current fortune.
    """,
    """
        Nancy: Our defenses stand tall, yet my mind is a whirlwind of concern. Can we ever truly rest?
        James: The clash of war fades, yet here I am, stomach growling amid our so-called victories. What are we fighting for?
        Lisa: Look around, friends! Our walls are sturdy, our coffers filling. Surely, this is a time for some cheer?
        Daniel: Satisfaction eludes me. Yes, we're safer, but at what cost? The hunger, the aggression—it's all too much.
        Paul: Our bellies aren't full, but our spirits should soar with these reinforced walls. Yet, why do I feel so uneasy?
        Nancy: It's the tension, ever-present. We eat, we build, yet the future is a shadowy path.
        Lisa: Cheerfulness is my mantle, but even I cannot ignore the pangs of hunger. Let's not lose sight of our basic needs.
        James: Impatience gnaws at me. We've traded wood for gold, but when will we trade fear for peace?
        Daniel: We're aggressive, not out of choice, but necessity. Yet, does that justify the discomfort we endure daily?
        Paul: Though I try to stay elated, restlessness seeps in. Are we merely surviving, or are we actually living?
    """,
    """
        Nancy: How much longer must we endure? Our walls are dust, and our stomachs growl in unison.
        James: Miserable and famished, that's what we are! The gold is no salve for our crumbling defenses and gnawing hunger.
        Lisa: Each day is heavier than the last. Our resources dwindle, and hope seems like a distant dream.
        Daniel: Moroseness grips me. We're guarded, yet vulnerable. What's the point of all this toil?
        Paul: Sorrow fills my days. We've lost so much, and for what? A few coins while our lives hang by a thread?
        Nancy: The gloom is pervasive. We're starving, yet we're asked to keep striving. Where is the light in all this darkness?
        Lisa: Tension mounts with each passing day. We must find a way to rise, or else succumb to despair.
        James: Outrage is all I feel. We've sacrificed too much, and yet our situation grows ever more dire.
        Daniel: Guarded but ravenous, I wonder, when will we see the fruits of our labor? When will we feel safe and sated?
        Paul: Anxious thoughts plague me. We're empty in more ways than one. It's time for change, but from where will it come?
    """,
    """
    Nancy: Resigned to our fate, we've built walls high, yet the excess weighs heavily. What becomes of us now?
    James: We're glutted with grain, yet my spirit is irritable. Fortified walls, yet I feel confined.
    Lisa: Stoicism is my refuge, but even I can't ignore the burden of this excess. We must find balance.
    Daniel: Our defenses stand tall, our granaries overflow, yet I remain watchful. Comfort breeds complacency.
    Paul: I yearn for a simpler time. Our bounty is vast, but so are our worries. What have we truly gained?
    Nancy: Acceptance is a bitter pill. We're passive, overwhelmed by our own prosperity. Where do we go from here?
    Lisa: Disinterest gnaws at me. We've succeeded in survival, but at what cost to our spirits?
    James: This irritation, it's not just the excess; it's the sense of defeat. Are we victors or just survivors?
    Daniel: Complacency is the enemy, even now. We must stay vigilant, or all this will be for naught.
    Paul: Concern fills me, not just for today, but for the future. Our walls may hold, but will our hearts?

    """,
    """
    Nancy: Panic seizes me as our food dwindles and walls weaken. What hope is left for us?
    James: Agitation is my constant companion. We're starving, our defenses falter, and yet we continue this endless struggle.
    Lisa: Nervousness pervades every moment. Can't we find a way out of this desperation?
    Daniel: Tension grips me. Starvation isn't just a threat; it's our reality. And still, we must fight.
    Paul: Worry consumes me. Our situation is dire, and yet we're expected to persevere. How?
    Nancy: Desperation claws at me. How did we end up here, with so little food and even less security?
    Lisa: Unsettled doesn't begin to cover it. Each day is a battle against hunger and decay.
    James: Incensed by our plight, I can't help but wonder, where did we go wrong? What's the cost of our so-called victories?
    Daniel: Fierce determination is all I have left. If we're to survive, we need more than gold; we need a miracle.
    Paul: Dismay fills my every thought. Our land, our people, all teetering on the brink. We need a change, and fast.

    """,
]


@pytest.mark.asyncio
async def test_db_launch():
    db = VectorDatabaseHandler.instance().init(":memory:")

    # TEST W/ ACTUAL API CALLS

    # Use db.insert() for OPENAI embeddings generator implementation
    # for input in input_list:
    #     db.insert(input)

    # TEST W/ MOCK DATA (Uses OPENAI generated embeddings)

    with open("data/embeddings/discussion_embeddings.json") as file:
        mock_data = json.load(file)

    # Insert each JSON object into the database
    for row in mock_data:
        db.mock_insert(row)

    # Prints database rows (embeddings are shortened)
    db.get_all()

    with open("data/embeddings/query_embeddings.json") as file:
        query_data = json.load(file)

    print("\n QUERIES \n")
    for row in query_data:
        res = db.query(row["embedding"])
        print(res)

    assert 1 == 2
