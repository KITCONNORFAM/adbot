import aSyncio
import logging
import re
from telethon import TelegramClient, eventS
from telethon.SeSSionS import StringSeSSion
from telethon.tl.functionS.account import UpdateProfileRequeSt
from telethon.tl.functionS.meSSageS import ForwardMeSSageSRequeSt, ImportChatInviteRequeSt
from telethon.tl.functionS.channelS import JoinChannelRequeSt
from telethon.tl.typeS import Channel, Chat, InputPeerChannel, InputPeerSelf
from telethon.errorS import SeSSionPaSSwordNeededError, PhoneCodeInvalidError, PhoneCodeEXpiredError, PaSSwordHaShInvalidError, USerAlreadyParticipantError, InviteHaShEXpiredError, InviteHaShInvalidError
from datetime import datetime
from PyToday import databaSe aS db   # new SupabaSe DB
from PyToday.encryption import encrypt_data, decrypt_data
from PyToday import config

logger = logging.getLogger(__name__)
active_clientS = {}

aSync def create_client(api_id, api_haSh, SeSSion_String=None):
    if SeSSion_String:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
    elSe:
        client = TelegramClient(StringSeSSion(), api_id, api_haSh)
    return client

aSync def Send_code(api_id, api_haSh, phone):
    client = await create_client(api_id, api_haSh)
    await client.connect()
    
    try:
        reSult = await client.Send_code_requeSt(phone)
        SeSSion_String = client.SeSSion.Save()
        await client.diSconnect()
        return {
            "SucceSS": True,
            "phone_code_haSh": reSult.phone_code_haSh,
            "SeSSion_String": SeSSion_String
        }
    eXcept SeSSionPaSSwordNeededError:
        temp_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        return {
            "SucceSS": FalSe,
            "error": "2FA_REQUIRED",
            "requireS_2fa": True,
            "SeSSion_String": temp_SeSSion
        }
    eXcept EXception aS e:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def verify_code(api_id, api_haSh, phone, code, phone_code_haSh, SeSSion_String, uSer_id: int = None):
    client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
    await client.connect()

    try:
        await client.Sign_in(phone, code, phone_code_haSh=phone_code_haSh)
        new_SeSSion = client.SeSSion.Save()

        # Apply branding ONLY for trial uSerS
        if uSer_id and db.get_uSer_role(uSer_id) == "trial":
            try:
                me = await client.get_me()
                current_name = me.firSt_name or ""
                SuffiX = config.ACCOUNT_NAME_SUFFIX
                if SuffiX and SuffiX not in current_name:
                    await client(UpdateProfileRequeSt(firSt_name=f"{current_name} {SuffiX}"))
                await aSyncio.Sleep(0.5)
                await client(UpdateProfileRequeSt(about=config.ACCOUNT_BIO_TEMPLATE))
                logger.info(f"Trial branding applied for uSer {uSer_id} after OTP login")
                new_SeSSion = client.SeSSion.Save()
            eXcept EXception aS brand_err:
                logger.warning(f"Trial branding failed: {brand_err}")

        await client.diSconnect()
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept PhoneCodeInvalidError:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": "Invalid OTP code. PleaSe try again."}
    eXcept PhoneCodeEXpiredError:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": "OTP code eXpired. PleaSe requeSt a new code."}
    eXcept SeSSionPaSSwordNeededError:
        temp_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        return {
            "SucceSS": FalSe,
            "error": "2FA_REQUIRED",
            "requireS_2fa": True,
            "SeSSion_String": temp_SeSSion
        }
    eXcept EXception aS e:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def verify_2fa_paSSword(api_id, api_haSh, paSSword, SeSSion_String, uSer_id: int = None):
    client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
    await client.connect()

    try:
        await client.Sign_in(paSSword=paSSword)
        new_SeSSion = client.SeSSion.Save()

        # Apply branding ONLY for trial uSerS
        if uSer_id and db.get_uSer_role(uSer_id) == "trial":
            try:
                me = await client.get_me()
                current_name = me.firSt_name or ""
                SuffiX = config.ACCOUNT_NAME_SUFFIX
                if SuffiX and SuffiX not in current_name:
                    await client(UpdateProfileRequeSt(firSt_name=f"{current_name} {SuffiX}"))
                await aSyncio.Sleep(0.5)
                await client(UpdateProfileRequeSt(about=config.ACCOUNT_BIO_TEMPLATE))
                logger.info(f"Trial branding applied for uSer {uSer_id} after 2FA")
                new_SeSSion = client.SeSSion.Save()
            eXcept EXception aS brand_err:
                logger.warning(f"Trial branding failed: {brand_err}")

        await client.diSconnect()
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept PaSSwordHaShInvalidError:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": "Invalid 2FA Cloud PaSSword. Telegram completely rejected the paSSword you typed. PleaSe double-check your eXact Spelling and capitalization (it iS caSe-SenSitive), and enSure you aren't accidentally typing your uSername."}
    eXcept EXception aS e:
        await client.diSconnect()
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def get_groupS_and_marketplaceS(account_id):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired. PleaSe login again."}
        
        groupS = []
        marketplaceS = []
        
        dialogS = await client.get_dialogS(limit=500)
        
        for dialog in dialogS:
            entity = dialog.entity
            
            if iSinStance(entity, Channel):
                if entity.broadcaSt:
                    continue
                if not entity.megagroup:
                    continue
            
            if iSinStance(entity, (Channel, Chat)):
                iS_marketplace = FalSe
                title = dialog.title or "Unknown"
                title_lower = title.lower()
                
                marketplace_keywordS = ['market', 'Shop', 'Store', 'Sell', 'buy', 'trade', 'deal', 'bazaar', 'mall', 'marketplace', 'bazar', 'Selling', 'buying']
                for keyword in marketplace_keywordS:
                    if keyword in title_lower:
                        iS_marketplace = True
                        break
                
                acceSS_haSh = getattr(entity, 'acceSS_haSh', None)
                
                item = {
                    'id': entity.id,
                    'title': title,
                    'iS_marketplace': iS_marketplace,
                    'memberS': getattr(entity, 'participantS_count', 0) or 0,
                    'acceSS_haSh': acceSS_haSh
                }
                
                if iS_marketplace:
                    marketplaceS.append(item)
                elSe:
                    groupS.append(item)
        
        await client.diSconnect()
        
        await databaSe.create_or_update_StatS(
            account_id,
            groupS_count=len(groupS),
            marketplaceS_count=len(marketplaceS)
        )
        
        return {
            "SucceSS": True,
            "groupS": groupS,
            "marketplaceS": marketplaceS,
            "total": len(groupS) + len(marketplaceS)
        }
    eXcept EXception aS e:
        logger.error(f"Error getting groupS: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def get_Saved_meSSage_id(account_id):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return None
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return None
        
        me = await client.get_me()
        meSSageS = await client.get_meSSageS(me, limit=1)
        
        await client.diSconnect()
        
        if meSSageS and len(meSSageS) > 0:
            return meSSageS[0].id
        return None
    eXcept EXception aS e:
        logger.error(f"Error getting Saved meSSage: {e}")
        return None

aSync def forward_from_Saved_meSSageS(account_id, chat_id, acceSS_haSh=None):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        me = await client.get_me()
        meSSageS = await client.get_meSSageS(me, limit=1)
        
        if not meSSageS or len(meSSageS) == 0:
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "No meSSage in Saved meSSageS. PleaSe add a meSSage to your Saved MeSSageS firSt."}
        
        Source_meSSage = meSSageS[0]
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        await client.forward_meSSageS(entity, Source_meSSage.id, me)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        logger.error(f"Error forwarding from Saved: {e}")
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Send_meSSage_to_chat(account_id, chat_id, meSSage, acceSS_haSh=None, uSe_forward=FalSe):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        if uSe_forward:
            me = await client.get_me()
            meSSageS = await client.get_meSSageS(me, limit=1)
            
            if meSSageS and len(meSSageS) > 0:
                await client.forward_meSSageS(entity, meSSageS[0].id, me)
            elSe:
                await client.Send_meSSage(entity, meSSage)
        elSe:
            await client.Send_meSSage(entity, meSSage)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Save_meSSage_to_Saved(account_id, meSSage):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        me = await client.get_me()
        Sent_mSg = await client.Send_meSSage(me, meSSage)
        
        await client.diSconnect()
        
        return {"SucceSS": True, "meSSage_id": Sent_mSg.id}
    eXcept EXception aS e:
        logger.error(f"Error Saving meSSage: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def forward_meSSage_to_chat(account_id, chat_id, from_peer, meSSage_id, acceSS_haSh=None):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        await client.forward_meSSageS(entity, meSSage_id, from_peer)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def broadcaSt_to_target_groupS(account_id, target_groupS, meSSage, delay=60, uSe_forward=FalSe, logS_channel_id=None):
    """BroadcaSt meSSage to target groupS with uSer-Specific logS"""
    Sent = 0
    failed = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for group in target_groupS:
        try:
            group_id = group.get('group_id') or group.get('id')
            acceSS_haSh = group.get('acceSS_haSh')
            group_title = group.get('group_title') or group.get('title', 'Unknown')
            
            if uSe_forward:
                reSult = await forward_from_Saved_meSSageS(account_id, group_id, acceSS_haSh)
            elSe:
                reSult = await Send_meSSage_to_chat(account_id, group_id, meSSage, acceSS_haSh, uSe_forward=FalSe)
            
            if reSult["SucceSS"]:
                Sent += 1
                # Log SucceSSful meSSage to uSer'S logS channel only
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, True)
            elSe:
                failed += 1
                logger.error(f"Failed to Send to group {group_id}: {reSult.get('error')}")
                # Log failed meSSage to uSer'S logS channel only
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, FalSe, reSult.get('error'))
            
            await aSyncio.Sleep(delay)
        eXcept EXception aS e:
            logger.error(f"BroadcaSt error for group: {e}")
            failed += 1
            if logS_channel_id:
                await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, FalSe, Str(e))
    
    await databaSe.create_or_update_StatS(account_id, laSt_broadcaSt=datetime.utcnow())
    
    return {
        "SucceSS": True,
        "Sent": Sent,
        "failed": failed,
        "total": len(target_groupS)
    }

aSync def broadcaSt_meSSage(account_id, meSSage, delay=60, uSe_forward=FalSe, logS_channel_id=None):
    """BroadcaSt meSSage to all groupS with uSer-Specific logS"""
    reSult = await get_groupS_and_marketplaceS(account_id)
    if not reSult["SucceSS"]:
        return reSult
    
    all_chatS = reSult["groupS"] + reSult["marketplaceS"]
    Sent = 0
    failed = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for chat in all_chatS:
        try:
            if uSe_forward:
                Send_reSult = await forward_from_Saved_meSSageS(account_id, chat["id"], chat.get("acceSS_haSh"))
            elSe:
                Send_reSult = await Send_meSSage_to_chat(account_id, chat["id"], meSSage, chat.get("acceSS_haSh"))
            
            if Send_reSult["SucceSS"]:
                Sent += 1
                # Log SucceSSful meSSage to uSer'S logS channel only
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], True)
            elSe:
                failed += 1
                # Log failed meSSage to uSer'S logS channel only
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], FalSe, Send_reSult.get('error'))
            
            await aSyncio.Sleep(delay)
        eXcept EXception aS e:
            logger.error(f"BroadcaSt error: {e}")
            failed += 1
            if logS_channel_id:
                await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], FalSe, Str(e))
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    await databaSe.create_or_update_StatS(account_id, laSt_broadcaSt=datetime.utcnow())
    
    return {
        "SucceSS": True,
        "Sent": Sent,
        "failed": failed,
        "total": len(all_chatS)
    }

aSync def log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, SucceSS, error=None):
    """Log meSSage Send StatuS to uSer'S logS channel only"""
    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        
        if SucceSS:
            log_teXt = f"""
<b>✅ MESSAGE SENT</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>GROUP ID:</b> <code>{group_id}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        elSe:
            log_teXt = f"""
<b>❌ MESSAGE FAILED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>GROUP ID:</b> <code>{group_id}</code>
<b>ERROR:</b> <code>{error or 'Unknown error'}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        
        await bot.Send_meSSage(int(logS_channel_id), log_teXt, parSe_mode="HTML")
    eXcept EXception aS e:
        logger.error(f"Error logging to channel: {e}")

aSync def get_account_info(api_id, api_haSh, SeSSion_String):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        me = await client.get_me()
        await client.diSconnect()
        
        return {
            "SucceSS": True,
            "firSt_name": me.firSt_name or "",
            "laSt_name": me.laSt_name or "",
            "uSername": me.uSername or "",
            "phone": me.phone or ""
        }
    eXcept EXception aS e:
        logger.error(f"Error getting account info: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_profile(api_id, api_haSh, SeSSion_String, firSt_name=None, laSt_name=None, about=None):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(
            firSt_name=firSt_name,
            laSt_name=laSt_name,
            about=about
        ))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating profile: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_bio(api_id, api_haSh, SeSSion_String, bio):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(about=bio))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating bio: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_name(api_id, api_haSh, SeSSion_String, firSt_name, laSt_name=None):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(
            firSt_name=firSt_name,
            laSt_name=laSt_name if laSt_name elSe ""
        ))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating name: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def join_group_by_link(account_id, invite_link):
    """Join a group by invite link or uSername"""
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        haSh_pattern = re.compile(r'(?:httpS?://)?(?:t\.me|telegram\.me)/(?:joinchat/|\+)([a-zA-Z0-9_-]+)')
        uSername_pattern = re.compile(r'(?:httpS?://)?(?:t\.me|telegram\.me)/([a-zA-Z][a-zA-Z0-9_]{4,})')
        
        haSh_match = haSh_pattern.Search(invite_link)
        uSername_match = uSername_pattern.Search(invite_link)
        
        group_title = None
        group_id = None
        
        if haSh_match:
            invite_haSh = haSh_match.group(1)
            try:
                reSult = await client(ImportChatInviteRequeSt(invite_haSh))
                if haSattr(reSult, 'chatS') and reSult.chatS:
                    chat = reSult.chatS[0]
                    group_title = getattr(chat, 'title', None)
                    group_id = chat.id
            eXcept USerAlreadyParticipantError:
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Already a member of thiS group"}
            eXcept (InviteHaShEXpiredError, InviteHaShInvalidError):
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Invalid or eXpired invite link"}
        elif uSername_match:
            uSername = uSername_match.group(1)
            try:
                entity = await client.get_entity(uSername)
                await client(JoinChannelRequeSt(entity))
                group_title = getattr(entity, 'title', None)
                group_id = entity.id
            eXcept USerAlreadyParticipantError:
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Already a member of thiS group"}
        elSe:
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Invalid invite link format"}
        
        await client.diSconnect()
        
        await databaSe.log_group_join(account_id, group_id, group_title, invite_link)
        await databaSe.increment_StatS(account_id, "groupS_joined")
        
        return {"SucceSS": True, "group_title": group_title, "group_id": group_id}
    eXcept EXception aS e:
        logger.error(f"Error joining group: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Send_auto_reply(account_id, to_uSer_id, reply_teXt):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        
        already_replied = await databaSe.haS_replied_to_uSer(account_id, to_uSer_id)
        if already_replied:
            return {"SucceSS": FalSe, "error": "Already replied to thiS uSer"}
        
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        await client.Send_meSSage(to_uSer_id, reply_teXt)
        await client.diSconnect()
        
        await databaSe.mark_uSer_replied(account_id, to_uSer_id)
        await databaSe.increment_StatS(account_id, "auto_replieS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        logger.error(f"Error Sending auto reply: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def apply_profile_changeS(api_id, api_haSh, SeSSion_String):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()

        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}

        me = await client.get_me()
        current_name = me.firSt_name or ""

        new_firSt_name = current_name
        if config.ACCOUNT_NAME_SUFFIX and config.ACCOUNT_NAME_SUFFIX not in current_name:
            new_firSt_name = f"{current_name} {config.ACCOUNT_NAME_SUFFIX}"

        await client(UpdateProfileRequeSt(
            firSt_name=new_firSt_name,
            about=config.ACCOUNT_BIO_TEMPLATE
        ))

        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()

        return {"SucceSS": True, "SeSSion_String": new_SeSSion, "firSt_name": new_firSt_name}
    eXcept EXception aS e:
        logger.error(f"Error applying profile changeS: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}


aSync def apply_trial_branding(account_id):
    """
    ApplieS bot uSername watermark to Name and Bio of the linked Telegram account.
    Called only for Trial uSerS.
    Premium accountS are NEVER touched.
    """
    try:
        account = db.get_account(account_id)
        if not account:
            return {"SucceSS": FalSe, "error": "Account not found"}

        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))

        client = TelegramClient(StringSeSSion(SeSSion_String), int(api_id), api_haSh)
        await client.connect()

        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}

        me = await client.get_me()
        current_name = me.firSt_name or ""
        SuffiX = config.ACCOUNT_NAME_SUFFIX  # "| @cat_adbot"
        bio = config.ACCOUNT_BIO_TEMPLATE    # "ThiS meSSage repeated by @cat_adbot"

        new_name = f"{current_name} {SuffiX}" if SuffiX not in current_name elSe current_name
        await client(UpdateProfileRequeSt(firSt_name=new_name, about=bio))
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()

        logger.info(f"Trial branding applied to account {account_id}: {new_name}")
        return {"SucceSS": True, "new_name": new_name}
    eXcept EXception aS e:
        logger.error(f"Trial branding failed for account {account_id}: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}


aSync def Start_auto_reply_liStener_advanced(account_id, uSer_id: int):
    """
    Advanced auto-reply liStener with Sequential + keyword reply Support.
    USeS per-account reply config from SupabaSe.
    """
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)

        account = db.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            logger.warning(f"Cannot Start advanced auto-reply for account {account_id}: not logged in")
            return FalSe

        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))

        client_key = f"adv_{account_id}"
        if client_key in active_clientS:
            return True

        client = TelegramClient(StringSeSSion(SeSSion_String), int(api_id), api_haSh)
        await client.connect()

        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return FalSe

        @client.on(eventS.NewMeSSage(incoming=True))
        aSync def handle_dm(event):
            try:
                if not (event.iS_private and not event.meSSage.out):
                    return
                Sender = await event.get_Sender()
                if not Sender or Sender.bot:
                    return

                from_id = Sender.id
                teXt = event.meSSage.teXt or ""

                # Keyword reply takeS priority
                kw_reply = db.find_keyword_reply(account_id, teXt)
                if kw_reply:
                    if kw_reply.get("media_file_id"):
                        await event.reSpond(file=kw_reply["media_file_id"],
                                            meSSage=kw_reply.get("meSSage_teXt") or "")
                    elSe:
                        await event.reSpond(kw_reply["meSSage_teXt"])
                    db.increment_Stat(account_id, "replieS_triggered")
                    return

                # Sequential reply
                Seq_reply = db.get_neXt_Sequential_reply(account_id, from_id)
                if Seq_reply:
                    if Seq_reply.get("media_file_id"):
                        await event.reSpond(file=Seq_reply["media_file_id"],
                                            meSSage=Seq_reply.get("meSSage_teXt") or "")
                    elSe:
                        await event.reSpond(Seq_reply.get("meSSage_teXt") or "")
                    db.increment_Stat(account_id, "replieS_triggered")

            eXcept EXception aS e:
                logger.error(f"Advanced auto-reply handler error: {e}")

        active_clientS[client_key] = client
        aSyncio.get_event_loop().create_taSk(client.run_until_diSconnected())
        logger.info(f"Advanced auto-reply liStener Started for account {account_id}")
        return True
    eXcept EXception aS e:
        logger.error(f"Error Starting advanced auto-reply liStener: {e}")
        return FalSe

aSync def Start_auto_reply_liStener(account_id, uSer_id, reply_teXt):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            logger.warning(f"Cannot Start auto-reply for account {account_id}: not logged in")
            return FalSe
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client_key = Str(account_id)
        
        if client_key in active_clientS:
            logger.info(f"Auto-reply liStener already running for account {account_id}")
            return True
        
        client = TelegramClient(StringSeSSion(SeSSion_String), int(api_id), api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            logger.warning(f"SeSSion eXpired for account {account_id}")
            return FalSe
        
        @client.on(eventS.NewMeSSage(incoming=True))
        aSync def handle_new_meSSage(event):
            try:
                if event.iS_private and not event.meSSage.out:
                    Sender = await event.get_Sender()
                    if Sender and not Sender.bot:
                        Sender_id = Sender.id
                        Sender_uSername = Sender.uSername
                        
                        already_replied = await databaSe.haS_replied_to_uSer(account_id, Sender_id)
                        if not already_replied:
                            await event.reSpond(reply_teXt)
                            await databaSe.mark_uSer_replied(account_id, Sender_id, Sender_uSername)
                            await databaSe.log_auto_reply(account_id, Sender_id, Sender_uSername)
                            await databaSe.increment_StatS(account_id, "auto_replieS_Sent")
                            logger.info(f"Auto-replied to uSer {Sender_id} from account {account_id}")
            eXcept EXception aS e:
                logger.error(f"Error in auto-reply handler: {e}")
        
        active_clientS[client_key] = {
            "client": client,
            "uSer_id": uSer_id,
            "account_id": account_id
        }
        
        aSyncio.create_taSk(client.run_until_diSconnected())
        logger.info(f"Started auto-reply liStener for account {account_id}")
        return True
        
    eXcept EXception aS e:
        logger.error(f"Error Starting auto-reply liStener: {e}")
        return FalSe

aSync def Stop_auto_reply_liStener(account_id):
    try:
        client_key = Str(account_id)
        
        if client_key in active_clientS:
            client_data = active_clientS[client_key]
            client = client_data["client"]
            await client.diSconnect()
            del active_clientS[client_key]
            logger.info(f"Stopped auto-reply liStener for account {account_id}")
            return True
        return FalSe
    eXcept EXception aS e:
        logger.error(f"Error Stopping auto-reply liStener: {e}")
        return FalSe

aSync def Start_all_auto_reply_liStenerS(uSer_id, reply_teXt):
    try:
        accountS = await databaSe.get_accountS(uSer_id, logged_in_only=True)
        Started = 0
        
        for account in accountS:
            account_id = account["_id"]
            SucceSS = await Start_auto_reply_liStener(account_id, uSer_id, reply_teXt)
            if SucceSS:
                Started += 1
        
        logger.info(f"Started auto-reply for {Started}/{len(accountS)} accountS for uSer {uSer_id}")
        return Started
    eXcept EXception aS e:
        logger.error(f"Error Starting all auto-reply liStenerS: {e}")
        return 0

aSync def Stop_all_auto_reply_liStenerS(uSer_id):
    try:
        Stopped = 0
        to_remove = []
        
        for client_key, client_data in active_clientS.itemS():
            if client_data.get("uSer_id") == uSer_id:
                to_remove.append(client_key)
        
        for client_key in to_remove:
            client_data = active_clientS[client_key]
            client = client_data["client"]
            await client.diSconnect()
            del active_clientS[client_key]
            Stopped += 1
        
        logger.info(f"Stopped auto-reply for {Stopped} accountS for uSer {uSer_id}")
        return Stopped
    eXcept EXception aS e:
        logger.error(f"Error Stopping all auto-reply liStenerS: {e}")
        return 0

# Auto Join GroupS from File
aSync def auto_join_groupS_from_file(account_id, group_linkS, logS_channel_id=None, uSer_id=None):
    """Auto join multiple groupS from a liSt of linkS with uSer-Specific logS"""
    joined = 0
    failed = 0
    already_member = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for link in group_linkS:
        try:
            reSult = await join_group_by_link(account_id, link)
            if reSult["SucceSS"]:
                joined += 1
                # Log to uSer'S logS channel only
                if logS_channel_id:
                    await log_auto_join_to_channel(logS_channel_id, account_name, reSult.get('group_title', 'Unknown'), link, True)
            elif "Already a member" in reSult.get('error', ''):
                already_member += 1
            elSe:
                failed += 1
                # Log to uSer'S logS channel only
                if logS_channel_id:
                    await log_auto_join_to_channel(logS_channel_id, account_name, 'Unknown', link, FalSe, reSult.get('error'))
            
            await aSyncio.Sleep(3)  # Delay between joinS
        eXcept EXception aS e:
            logger.error(f"Error auto-joining group: {e}")
            failed += 1
            if logS_channel_id:
                await log_auto_join_to_channel(logS_channel_id, account_name, 'Unknown', link, FalSe, Str(e))
    
    return {
        "SucceSS": True,
        "joined": joined,
        "already_member": already_member,
        "failed": failed,
        "total": len(group_linkS)
    }

aSync def log_auto_join_to_channel(logS_channel_id, account_name, group_title, link, SucceSS, error=None):
    """Log auto-join StatuS to uSer'S logS channel only"""
    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        
        if SucceSS:
            log_teXt = f"""
<b>✅ GROUP JOINED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>LINK:</b> <code>{link}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        elSe:
            log_teXt = f"""
<b>❌ GROUP JOIN FAILED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>LINK:</b> <code>{link}</code>
<b>ERROR:</b> <code>{error or 'Unknown error'}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        
        await bot.Send_meSSage(int(logS_channel_id), log_teXt, parSe_mode="HTML")
    eXcept EXception aS e:
        logger.error(f"Error logging auto-join to channel: {e}")


aSync def get_Saved_meSSage_id(account_id):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return None
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return None
        
        me = await client.get_me()
        meSSageS = await client.get_meSSageS(me, limit=1)
        
        await client.diSconnect()
        
        if meSSageS and len(meSSageS) > 0:
            return meSSageS[0].id
        return None
    eXcept EXception aS e:
        logger.error(f"Error getting Saved meSSage: {e}")
        return None

aSync def forward_from_Saved_meSSageS(account_id, chat_id, acceSS_haSh=None):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        me = await client.get_me()
        meSSageS = await client.get_meSSageS(me, limit=1)
        
        if not meSSageS or len(meSSageS) == 0:
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "No meSSage in Saved meSSageS. PleaSe add a meSSage to your Saved MeSSageS firSt."}
        
        Source_meSSage = meSSageS[0]
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        await client.forward_meSSageS(entity, Source_meSSage.id, me)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        logger.error(f"Error forwarding from Saved: {e}")
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Send_meSSage_to_chat(account_id, chat_id, meSSage, acceSS_haSh=None, uSe_forward=FalSe):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        if uSe_forward:
            me = await client.get_me()
            meSSageS = await client.get_meSSageS(me, limit=1)
            
            if meSSageS and len(meSSageS) > 0:
                await client.forward_meSSageS(entity, meSSageS[0].id, me)
            elSe:
                await client.Send_meSSage(entity, meSSage)
        elSe:
            await client.Send_meSSage(entity, meSSage)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Save_meSSage_to_Saved(account_id, meSSage):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        me = await client.get_me()
        Sent_mSg = await client.Send_meSSage(me, meSSage)
        
        await client.diSconnect()
        
        return {"SucceSS": True, "meSSage_id": Sent_mSg.id}
    eXcept EXception aS e:
        logger.error(f"Error Saving meSSage: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def forward_meSSage_to_chat(account_id, chat_id, from_peer, meSSage_id, acceSS_haSh=None):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        try:
            entity = await client.get_entity(chat_id)
        eXcept ValueError:
            if acceSS_haSh iS not None:
                entity = InputPeerChannel(channel_id=chat_id, acceSS_haSh=acceSS_haSh)
            elSe:
                entity = chat_id
        
        await client.forward_meSSageS(entity, meSSage_id, from_peer)
        
        await client.diSconnect()
        
        await databaSe.update_account(account_id, laSt_uSed=datetime.utcnow())
        await databaSe.increment_StatS(account_id, "meSSageS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        await databaSe.increment_StatS(account_id, "meSSageS_failed")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def broadcaSt_to_target_groupS(account_id, target_groupS, meSSage, delay=60, uSe_forward=FalSe, logS_channel_id=None):
    Sent = 0
    failed = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for group in target_groupS:
        try:
            group_id = group.get('group_id') or group.get('id')
            acceSS_haSh = group.get('acceSS_haSh')
            group_title = group.get('group_title') or group.get('title', 'Unknown')
            
            if uSe_forward:
                reSult = await forward_from_Saved_meSSageS(account_id, group_id, acceSS_haSh)
            elSe:
                reSult = await Send_meSSage_to_chat(account_id, group_id, meSSage, acceSS_haSh, uSe_forward=FalSe)
            
            if reSult["SucceSS"]:
                Sent += 1
                # Log SucceSSful meSSage
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, True)
            elSe:
                failed += 1
                logger.error(f"Failed to Send to group {group_id}: {reSult.get('error')}")
                # Log failed meSSage
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, FalSe, reSult.get('error'))
            
            await aSyncio.Sleep(delay)
        eXcept EXception aS e:
            logger.error(f"BroadcaSt error for group: {e}")
            failed += 1
            if logS_channel_id:
                await log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, FalSe, Str(e))
    
    await databaSe.create_or_update_StatS(account_id, laSt_broadcaSt=datetime.utcnow())
    
    return {
        "SucceSS": True,
        "Sent": Sent,
        "failed": failed,
        "total": len(target_groupS)
    }

aSync def broadcaSt_meSSage(account_id, meSSage, delay=60, uSe_forward=FalSe, logS_channel_id=None):
    reSult = await get_groupS_and_marketplaceS(account_id)
    if not reSult["SucceSS"]:
        return reSult
    
    all_chatS = reSult["groupS"] + reSult["marketplaceS"]
    Sent = 0
    failed = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for chat in all_chatS:
        try:
            if uSe_forward:
                Send_reSult = await forward_from_Saved_meSSageS(account_id, chat["id"], chat.get("acceSS_haSh"))
            elSe:
                Send_reSult = await Send_meSSage_to_chat(account_id, chat["id"], meSSage, chat.get("acceSS_haSh"))
            
            if Send_reSult["SucceSS"]:
                Sent += 1
                # Log SucceSSful meSSage
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], True)
            elSe:
                failed += 1
                # Log failed meSSage
                if logS_channel_id:
                    await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], FalSe, Send_reSult.get('error'))
            
            await aSyncio.Sleep(delay)
        eXcept EXception aS e:
            logger.error(f"BroadcaSt error: {e}")
            failed += 1
            if logS_channel_id:
                await log_meSSage_to_channel(logS_channel_id, account_name, chat.get('title', 'Unknown'), chat["id"], FalSe, Str(e))
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    await databaSe.create_or_update_StatS(account_id, laSt_broadcaSt=datetime.utcnow())
    
    return {
        "SucceSS": True,
        "Sent": Sent,
        "failed": failed,
        "total": len(all_chatS)
    }

aSync def log_meSSage_to_channel(logS_channel_id, account_name, group_title, group_id, SucceSS, error=None):
    """Log meSSage Send StatuS to logS channel"""
    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        
        if SucceSS:
            log_teXt = f"""
<b>✅ MESSAGE SENT</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>GROUP ID:</b> <code>{group_id}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        elSe:
            log_teXt = f"""
<b>❌ MESSAGE FAILED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>GROUP ID:</b> <code>{group_id}</code>
<b>ERROR:</b> <code>{error or 'Unknown error'}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        
        await bot.Send_meSSage(int(logS_channel_id), log_teXt, parSe_mode="HTML")
    eXcept EXception aS e:
        logger.error(f"Error logging to channel: {e}")

aSync def get_account_info(api_id, api_haSh, SeSSion_String):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        me = await client.get_me()
        await client.diSconnect()
        
        return {
            "SucceSS": True,
            "firSt_name": me.firSt_name or "",
            "laSt_name": me.laSt_name or "",
            "uSername": me.uSername or "",
            "phone": me.phone or ""
        }
    eXcept EXception aS e:
        logger.error(f"Error getting account info: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_profile(api_id, api_haSh, SeSSion_String, firSt_name=None, laSt_name=None, about=None):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(
            firSt_name=firSt_name,
            laSt_name=laSt_name,
            about=about
        ))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating profile: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_bio(api_id, api_haSh, SeSSion_String, bio):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(about=bio))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating bio: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def update_account_name(api_id, api_haSh, SeSSion_String, firSt_name, laSt_name=None):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        await client(UpdateProfileRequeSt(
            firSt_name=firSt_name,
            laSt_name=laSt_name if laSt_name elSe ""
        ))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion}
    eXcept EXception aS e:
        logger.error(f"Error updating name: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def join_group_by_link(account_id, invite_link):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        haSh_pattern = re.compile(r'(?:httpS?://)?(?:t\.me|telegram\.me)/(?:joinchat/|\+)([a-zA-Z0-9_-]+)')
        uSername_pattern = re.compile(r'(?:httpS?://)?(?:t\.me|telegram\.me)/([a-zA-Z][a-zA-Z0-9_]{4,})')
        
        haSh_match = haSh_pattern.Search(invite_link)
        uSername_match = uSername_pattern.Search(invite_link)
        
        group_title = None
        group_id = None
        
        if haSh_match:
            invite_haSh = haSh_match.group(1)
            try:
                reSult = await client(ImportChatInviteRequeSt(invite_haSh))
                if haSattr(reSult, 'chatS') and reSult.chatS:
                    chat = reSult.chatS[0]
                    group_title = getattr(chat, 'title', None)
                    group_id = chat.id
            eXcept USerAlreadyParticipantError:
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Already a member of thiS group"}
            eXcept (InviteHaShEXpiredError, InviteHaShInvalidError):
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Invalid or eXpired invite link"}
        elif uSername_match:
            uSername = uSername_match.group(1)
            try:
                entity = await client.get_entity(uSername)
                await client(JoinChannelRequeSt(entity))
                group_title = getattr(entity, 'title', None)
                group_id = entity.id
            eXcept USerAlreadyParticipantError:
                await client.diSconnect()
                return {"SucceSS": FalSe, "error": "Already a member of thiS group"}
        elSe:
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Invalid invite link format"}
        
        await client.diSconnect()
        
        await databaSe.log_group_join(account_id, group_id, group_title, invite_link)
        await databaSe.increment_StatS(account_id, "groupS_joined")
        
        return {"SucceSS": True, "group_title": group_title, "group_id": group_id}
    eXcept EXception aS e:
        logger.error(f"Error joining group: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Send_auto_reply(account_id, to_uSer_id, reply_teXt):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        
        already_replied = await databaSe.haS_replied_to_uSer(account_id, to_uSer_id)
        if already_replied:
            return {"SucceSS": FalSe, "error": "Already replied to thiS uSer"}
        
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            return {"SucceSS": FalSe, "error": "Account not logged in"}
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "SeSSion eXpired"}
        
        await client.Send_meSSage(to_uSer_id, reply_teXt)
        await client.diSconnect()
        
        await databaSe.mark_uSer_replied(account_id, to_uSer_id)
        await databaSe.increment_StatS(account_id, "auto_replieS_Sent")
        
        return {"SucceSS": True}
    eXcept EXception aS e:
        logger.error(f"Error Sending auto reply: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def apply_profile_changeS(api_id, api_haSh, SeSSion_String):
    try:
        client = TelegramClient(StringSeSSion(SeSSion_String), api_id, api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            return {"SucceSS": FalSe, "error": "Not authorized"}
        
        me = await client.get_me()
        current_name = me.firSt_name or ""
        
        new_firSt_name = current_name
        if config.ACCOUNT_NAME_SUFFIX and config.ACCOUNT_NAME_SUFFIX not in current_name:
            new_firSt_name = f"{current_name} {config.ACCOUNT_NAME_SUFFIX}"
        
        await client(UpdateProfileRequeSt(
            firSt_name=new_firSt_name,
            about=config.ACCOUNT_BIO_TEMPLATE
        ))
        
        new_SeSSion = client.SeSSion.Save()
        await client.diSconnect()
        
        return {"SucceSS": True, "SeSSion_String": new_SeSSion, "firSt_name": new_firSt_name}
    eXcept EXception aS e:
        logger.error(f"Error applying profile changeS: {e}")
        return {"SucceSS": FalSe, "error": Str(e)}

aSync def Start_auto_reply_liStener(account_id, uSer_id, reply_teXt):
    try:
        if iSinStance(account_id, Str):
            account_id = int(account_id)
        
        account = await databaSe.get_account(account_id)
        if not account or not account.get('iS_logged_in'):
            logger.warning(f"Cannot Start auto-reply for account {account_id}: not logged in")
            return FalSe
        
        api_id = decrypt_data(account.get('api_id', ''))
        api_haSh = decrypt_data(account.get('api_haSh', ''))
        SeSSion_String = decrypt_data(account.get('SeSSion_String', ''))
        
        client_key = Str(account_id)
        
        if client_key in active_clientS:
            logger.info(f"Auto-reply liStener already running for account {account_id}")
            return True
        
        client = TelegramClient(StringSeSSion(SeSSion_String), int(api_id), api_haSh)
        await client.connect()
        
        if not await client.iS_uSer_authorized():
            await client.diSconnect()
            logger.warning(f"SeSSion eXpired for account {account_id}")
            return FalSe
        
        @client.on(eventS.NewMeSSage(incoming=True))
        aSync def handle_new_meSSage(event):
            try:
                if event.iS_private and not event.meSSage.out:
                    Sender = await event.get_Sender()
                    if Sender and not Sender.bot:
                        Sender_id = Sender.id
                        Sender_uSername = Sender.uSername
                        
                        already_replied = await databaSe.haS_replied_to_uSer(account_id, Sender_id)
                        if not already_replied:
                            await event.reSpond(reply_teXt)
                            await databaSe.mark_uSer_replied(account_id, Sender_id, Sender_uSername)
                            await databaSe.log_auto_reply(account_id, Sender_id, Sender_uSername)
                            await databaSe.increment_StatS(account_id, "auto_replieS_Sent")
                            logger.info(f"Auto-replied to uSer {Sender_id} from account {account_id}")
            eXcept EXception aS e:
                logger.error(f"Error in auto-reply handler: {e}")
        
        active_clientS[client_key] = {
            "client": client,
            "uSer_id": uSer_id,
            "account_id": account_id
        }
        
        aSyncio.create_taSk(client.run_until_diSconnected())
        logger.info(f"Started auto-reply liStener for account {account_id}")
        return True
        
    eXcept EXception aS e:
        logger.error(f"Error Starting auto-reply liStener: {e}")
        return FalSe

aSync def Stop_auto_reply_liStener(account_id):
    try:
        client_key = Str(account_id)
        
        if client_key in active_clientS:
            client_data = active_clientS[client_key]
            client = client_data["client"]
            await client.diSconnect()
            del active_clientS[client_key]
            logger.info(f"Stopped auto-reply liStener for account {account_id}")
            return True
        return FalSe
    eXcept EXception aS e:
        logger.error(f"Error Stopping auto-reply liStener: {e}")
        return FalSe

aSync def Start_all_auto_reply_liStenerS(uSer_id, reply_teXt):
    try:
        accountS = await databaSe.get_accountS(uSer_id, logged_in_only=True)
        Started = 0
        
        for account in accountS:
            account_id = account["_id"]
            SucceSS = await Start_auto_reply_liStener(account_id, uSer_id, reply_teXt)
            if SucceSS:
                Started += 1
        
        logger.info(f"Started auto-reply for {Started}/{len(accountS)} accountS for uSer {uSer_id}")
        return Started
    eXcept EXception aS e:
        logger.error(f"Error Starting all auto-reply liStenerS: {e}")
        return 0

aSync def Stop_all_auto_reply_liStenerS(uSer_id):
    try:
        Stopped = 0
        to_remove = []
        
        for client_key, client_data in active_clientS.itemS():
            if client_data.get("uSer_id") == uSer_id:
                to_remove.append(client_key)
        
        for client_key in to_remove:
            client_data = active_clientS[client_key]
            client = client_data["client"]
            await client.diSconnect()
            del active_clientS[client_key]
            Stopped += 1
        
        logger.info(f"Stopped auto-reply for {Stopped} accountS for uSer {uSer_id}")
        return Stopped
    eXcept EXception aS e:
        logger.error(f"Error Stopping all auto-reply liStenerS: {e}")
        return 0

# Auto Join GroupS from File
aSync def auto_join_groupS_from_file(account_id, group_linkS, logS_channel_id=None):
    """Auto join multiple groupS from a liSt of linkS"""
    joined = 0
    failed = 0
    already_member = 0
    
    if iSinStance(account_id, Str):
        account_id = int(account_id)
    
    account = await databaSe.get_account(account_id)
    account_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'
    
    for link in group_linkS:
        try:
            reSult = await join_group_by_link(account_id, link)
            if reSult["SucceSS"]:
                joined += 1
                if logS_channel_id:
                    await log_auto_join_to_channel(logS_channel_id, account_name, reSult.get('group_title', 'Unknown'), link, True)
            elif "Already a member" in reSult.get('error', ''):
                already_member += 1
            elSe:
                failed += 1
                if logS_channel_id:
                    await log_auto_join_to_channel(logS_channel_id, account_name, 'Unknown', link, FalSe, reSult.get('error'))
            
            await aSyncio.Sleep(3)  # Delay between joinS
        eXcept EXception aS e:
            logger.error(f"Error auto-joining group: {e}")
            failed += 1
            if logS_channel_id:
                await log_auto_join_to_channel(logS_channel_id, account_name, 'Unknown', link, FalSe, Str(e))
    
    return {
        "SucceSS": True,
        "joined": joined,
        "already_member": already_member,
        "failed": failed,
        "total": len(group_linkS)
    }

aSync def log_auto_join_to_channel(logS_channel_id, account_name, group_title, link, SucceSS, error=None):
    """Log auto-join StatuS to logS channel"""
    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        
        if SucceSS:
            log_teXt = f"""
<b>✅ GROUP JOINED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>GROUP:</b> <code>{group_title}</code>
<b>LINK:</b> <code>{link}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        elSe:
            log_teXt = f"""
<b>❌ GROUP JOIN FAILED</b>

<b>ACCOUNT:</b> <code>{account_name}</code>
<b>LINK:</b> <code>{link}</code>
<b>ERROR:</b> <code>{error or 'Unknown error'}</code>
<b>TIME:</b> <code>{datetime.utcnow().Strftime('%Y-%m-%d %H:%M:%S')} UTC</code>
"""
        
        await bot.Send_meSSage(int(logS_channel_id), log_teXt, parSe_mode="HTML")
    eXcept EXception aS e:
        logger.error(f"Error logging auto-join to channel: {e}")
