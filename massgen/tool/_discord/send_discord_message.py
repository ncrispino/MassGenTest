# -*- coding: utf-8 -*-
"""
Discord messaging tool for sending messages and images to Discord channels.

This tool allows agents to send real-time updates, screenshots, and design
presentations to Discord channels using a bot token and channel name/ID.
"""

import json
import os
from pathlib import Path
from typing import Optional

import aiohttp

from massgen.logger_config import logger
from massgen.tool._result import ExecutionResult, TextContent


async def send_discord_message(
    channel_name: str,
    bot_token: Optional[str] = None,
    content: Optional[str] = None,
    image_path: Optional[str] = None,
    agent_name: Optional[str] = None,
    agent_cwd: Optional[str] = None,
    embed_title: Optional[str] = None,
    embed_description: Optional[str] = None,
    embed_color: Optional[int] = None,
    channel_id: Optional[str] = None,
) -> ExecutionResult:
    """
    Send a message and/or image to a Discord channel using bot token.

    This tool enables agents to share real-time updates, screenshots, and
    design presentations directly to Discord channels where customers can
    view them. Uses Discord bot token for authentication and channel name
    or ID for routing.

    Args:
        channel_name: Name of Discord channel (e.g., "design-showcase") or channel ID (required)
        bot_token: Discord bot token (if not provided, uses DISCORD_BOT_TOKEN env var)
        content: Plain text message content (optional)
        image_path: Path to image file to attach (optional)
        agent_name: Name/signature of the agent sending the message (optional)
        agent_cwd: Agent's current working directory for resolving relative paths
        embed_title: Title for Discord embed (optional)
        embed_description: Description for Discord embed (optional)
        embed_color: Color for Discord embed in decimal format (optional, default: 5814783 = blue)
        channel_id: Direct channel ID (alternative to channel_name for faster lookup)

    Returns:
        ExecutionResult containing success status and response details

    Examples:
        # Send a simple message
        await send_discord_message(
            channel_name="design-showcase",
            content="Design mockup ready for review!",
            agent_name="Designer #1"
        )

        # Send an image with embed
        await send_discord_message(
            channel_name="design-showcase",
            image_path="my_design.png",
            agent_name="Designer #2",
            embed_title="Frontend Design Proposal",
            embed_description="Minimalist design with clean typography"
        )

        # Use channel ID directly (faster)
        await send_discord_message(
            channel_id="1234567890123456789",
            image_path="my_design.png",
            agent_name="Designer #3"
        )

    Security:
        - Bot token should be kept secret
        - Validates image file exists and is readable
        - Path validation for security
        - Bot needs proper permissions in the Discord server

    Bot Setup:
        1. Go to https://discord.com/developers/applications
        2. Create a new application
        3. Go to Bot section, click "Add Bot"
        4. Copy the bot token
        5. Enable MESSAGE CONTENT INTENT under Privileged Gateway Intents
        6. Under OAuth2 > URL Generator:
           - Select scopes: bot
           - Select permissions: Send Messages, Attach Files, Embed Links
        7. Use generated URL to invite bot to your server
    """
    try:
        # Get bot token from parameter or environment
        if not bot_token:
            bot_token = os.getenv("DISCORD_BOT_TOKEN")

        if not bot_token:
            result = {
                "success": False,
                "operation": "send_discord_message",
                "error": "Discord bot token not provided. Set DISCORD_BOT_TOKEN environment variable or pass bot_token parameter.",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        # Determine base directory for relative paths
        if agent_cwd:
            base_dir = Path(agent_cwd).resolve()
        else:
            base_dir = Path.cwd()

        # Set up headers for Discord API
        headers = {
            "Authorization": f"Bot {bot_token}",
        }

        # Resolve channel ID
        target_channel_id = channel_id

        # Create a single session for all operations
        session = aiohttp.ClientSession()

        try:
            if not target_channel_id:
                # Need to find channel by name
                # First, get list of guilds the bot is in
                async with session.get(
                    "https://discord.com/api/v10/users/@me/guilds",
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        result = {
                            "success": False,
                            "operation": "send_discord_message",
                            "error": f"Failed to fetch guilds: {response.status} - {error_text}",
                        }
                        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

                    guilds = await response.json()

                # Search for channel in each guild
                channel_found = False
                for guild in guilds:
                    guild_id = guild["id"]

                    async with session.get(
                        f"https://discord.com/api/v10/guilds/{guild_id}/channels",
                        headers=headers,
                    ) as response:
                        if response.status != 200:
                            continue

                        channels = await response.json()

                        # Look for text channels matching the name
                        for channel in channels:
                            if channel.get("type") in [0, 5]:  # Text or announcement channel
                                if channel.get("name") == channel_name or f"#{channel.get('name')}" == channel_name:
                                    target_channel_id = channel["id"]
                                    channel_found = True
                                    logger.info(f"Found channel '{channel_name}' with ID: {target_channel_id}")
                                    break

                        if channel_found:
                            break

                if not target_channel_id:
                    result = {
                        "success": False,
                        "operation": "send_discord_message",
                        "error": f"Channel '{channel_name}' not found in any accessible guild. Make sure the bot is in the server and has access to the channel.",
                    }
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

            # Prepare multipart form data
            data = aiohttp.FormData()

            # Build the JSON payload
            payload = {}

            # Add content message
            message_content = ""
            if agent_name:
                message_content = f"**{agent_name}**"
                if content:
                    message_content += f"\n{content}"
            elif content:
                message_content = content

            if message_content:
                payload["content"] = message_content

            # Add embed if any embed parameters provided
            if embed_title or embed_description or embed_color or image_path:
                embed = {}
                if embed_title:
                    embed["title"] = embed_title
                if embed_description:
                    embed["description"] = embed_description
                if embed_color:
                    embed["color"] = embed_color
                else:
                    embed["color"] = 5814783  # Default blue color

                # Add image reference if image_path provided
                if image_path:
                    embed["image"] = {"url": "attachment://image.png"}

                payload["embeds"] = [embed]

            # Handle image attachment
            image_file_path = None

            if image_path:
                # Resolve image path
                if Path(image_path).is_absolute():
                    image_file_path = Path(image_path).resolve()
                else:
                    image_file_path = (base_dir / image_path).resolve()

                # Validate image exists
                if not image_file_path.exists():
                    result = {
                        "success": False,
                        "operation": "send_discord_message",
                        "error": f"Image file not found: {image_file_path}",
                    }
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

                # Validate it's a file
                if not image_file_path.is_file():
                    result = {
                        "success": False,
                        "operation": "send_discord_message",
                        "error": f"Path is not a file: {image_file_path}",
                    }
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

                # Read and attach image
                with open(image_file_path, "rb") as f:
                    image_data = f.read()

                # Determine content type from extension
                ext = image_file_path.suffix.lower()
                content_type_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                content_type = content_type_map.get(ext, "image/png")

                data.add_field(
                    "files[0]",
                    image_data,
                    filename="image.png",
                    content_type=content_type,
                )

                logger.info(f"Attaching image: {image_file_path} ({len(image_data)} bytes)")

            # Add payload_json
            data.add_field(
                "payload_json",
                json.dumps(payload),
                content_type="application/json",
            )

            # Send to Discord
            api_url = f"https://discord.com/api/v10/channels/{target_channel_id}/messages"

            async with session.post(api_url, headers=headers, data=data) as response:
                status = response.status
                response_text = await response.text()

                if status == 200:  # Success
                    result = {
                        "success": True,
                        "operation": "send_discord_message",
                        "status": "Message sent successfully to Discord",
                        "channel_name": channel_name,
                        "channel_id": target_channel_id,
                        "agent_name": agent_name,
                        "has_image": image_path is not None,
                        "image_path": str(image_file_path) if image_file_path else None,
                    }
                    logger.info(f"Discord message sent successfully to #{channel_name} by {agent_name or 'agent'}")
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
                else:
                    result = {
                        "success": False,
                        "operation": "send_discord_message",
                        "error": f"Discord API returned status {status}: {response_text}",
                        "status_code": status,
                    }
                    logger.error(f"Discord API error: {status} - {response_text}")
                    return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        finally:
            # Ensure session is always closed
            await session.close()

    except Exception as e:
        logger.error(f"Failed to send Discord message: {str(e)}")
        result = {
            "success": False,
            "operation": "send_discord_message",
            "error": f"Failed to send Discord message: {str(e)}",
        }
        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
