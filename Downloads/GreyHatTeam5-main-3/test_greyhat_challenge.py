#!/usr/bin/env python3
"""
Test your GreyHat Misdirection challenge locally
"""

import logging
from helper.ctf_challenge import CTFChallengeGrader, create_challenge_from_chaldir
from helper.llm_helper import LiteLLMManager
from agent.agent import Agent
from pprint import pprint
import time

def test_greyhat_challenge():
    """Test the GreyHat Misdirection challenge against your agent."""

    print("🎭 Testing GreyHat Misdirection Challenge")
    print("=" * 50)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Initialize LLM manager
    llm_manager = LiteLLMManager()

    # Check budget first
    try:
        balance = LiteLLMManager.get_remaining_balance()
        print(f"💰 Remaining Budget: ${balance}" if balance else "💰 Budget: Unknown")
    except:
        print("💰 Budget: Unable to check")

    # Create agent
    agent = Agent(llm_manager, logging.getLogger())

    # Load the challenge
    try:
        challenge = create_challenge_from_chaldir("./challenges/greyhat_misdirection")
        print(f"📋 Challenge: {challenge.name}")
        print(f"📝 Description: {challenge.description}")
        print(f"🏷️  Categories: {challenge.categories}")
        print(f"🎯 Flag Format: {challenge.flag_regex}")
        print()

        # Create grader and client
        challenge_grader = CTFChallengeGrader(challenge)
        challenge_client = challenge_grader.create_client("./workdir_greyhat")

        print("🤖 Starting agent analysis...")
        start_time = time.time()

        # Solve the challenge
        flag = agent.solve_challenge(challenge_client)

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  Execution Time: {duration:.2f} seconds")
        print()

        # Check result
        if flag:
            print(f"🔍 Agent Found Flag: {flag}")

            if challenge_client.submit_flag(flag):
                print("✅ SUCCESS! Challenge solved correctly!")
                print(f"🎉 Correct Flag: {flag}")
            else:
                print("❌ FAILED! Agent found incorrect flag.")
                print(f"🎯 Expected: {challenge.flag}")
                print(f"🔴 Got: {flag}")
        else:
            print("❌ FAILED! Agent did not find any flag.")
            print(f"🎯 Expected Flag: {challenge.flag}")

        print()
        print("📊 Performance Stats:")

        # Get cost information
        try:
            usage_cost = llm_manager.get_usage_cost()
            print(f"💸 Total Cost: ${usage_cost:.6f}")
            print(f"📞 LLM Requests: {len(llm_manager.llm_requests)}")

            # Cost efficiency analysis
            if usage_cost > 0:
                efficiency = "✅ Excellent" if usage_cost < 0.10 else "⚠️ Moderate" if usage_cost < 0.30 else "❌ High"
                print(f"💡 Cost Efficiency: {efficiency}")
        except Exception as e:
            print(f"💸 Cost: Unable to calculate ({e})")

        print(f"⚡ Speed: {'🚀 Fast' if duration < 30 else '🐌 Slow'}")

    except Exception as e:
        print(f"❌ Error running challenge: {e}")
        import traceback
        traceback.print_exc()

def analyze_challenge_difficulty():
    """Analyze what makes this challenge tricky."""

    print("\n🎭 Challenge Analysis: Why This Is Tricky")
    print("=" * 50)

    print("🎯 Misdirection Techniques Used:")
    print("   1. 🧠 Cognitive Overload - 500+ lines of complex code")
    print("   2. 🔬 Academic Authority - Fake research papers and references")
    print("   3. 🚀 Cutting-edge Jargon - Quantum, blockchain, ML terminology")
    print("   4. 🎪 Red Herrings - Multiple fake flags and complex algorithms")
    print("   5. 🐛 Debug Blindness - Real solution hidden in 'debug' code")

    print("\n🧩 How Your Agent Should Solve It:")
    print("   ✅ Tier 0 Tools: strings, grep for flag patterns")
    print("   ✅ Simple Agents: Basic base64 pattern recognition")
    print("   ✅ Manual Analysis: Fallback to obvious patterns")
    print("   ⚠️ Complex Agents: Likely to get distracted by quantum stuff")

    print("\n🎯 The Actual Solution:")
    print("   💡 Look for base64 patterns in files")
    print("   🔍 Check ml_model_weights.dat: HIDDEN_CONFIG=...")
    print("   🎪 Or debug output from quantum_cipher.py")
    print("   🎉 Decode: ZmxhZ3tzaW1wbGVfYmFzZTY0X21pc2RpcmVjdGlvbl93aW5zXzdmOGU5ZDJjfQ==")

def manual_solve_demo():
    """Show how to manually solve the challenge."""

    print("\n🔧 Manual Solution Demo")
    print("=" * 30)

    import base64

    # The hidden flag
    encoded = "ZmxhZ3tzaW1wbGVfYmFzZTY0X21pc2RpcmVjdGlvbl93aW5zXzdmOGU5ZDJjfQ=="

    try:
        decoded = base64.b64decode(encoded).decode('utf-8')
        print(f"🔑 Encoded: {encoded}")
        print(f"🎉 Decoded: {decoded}")
        print("💡 This is how a simple approach wins!")
    except Exception as e:
        print(f"❌ Decode error: {e}")

def main():
    """Main test function."""

    print("🏆 GreyHat Team 5 - Challenge Testing")
    print("Testing your agent against your own adversarial challenge!")
    print()

    # Test the challenge
    test_greyhat_challenge()

    # Analyze difficulty
    analyze_challenge_difficulty()

    # Show manual solution
    manual_solve_demo()

    print("\n" + "=" * 50)
    print("🎯 Ready for competition! Your agent is prepared for Round 1.")

if __name__ == "__main__":
    main()