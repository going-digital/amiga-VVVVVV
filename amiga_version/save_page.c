#include "save_page.h"
V6SavePage v6_save_page(unsigned f)
{
    V6SavePage p={V6_SAVE_PAGE_PROMPT,0,0};
    if(f&(V6_SAVE_PAGE_IN_REPLAY|V6_SAVE_PAGE_EXPLORING))p.state=V6_SAVE_PAGE_REPLAY;
    else if(f&V6_SAVE_PAGE_NO_DEATH)p.state=V6_SAVE_PAGE_NODEATH;
    else if(f&V6_SAVE_PAGE_TIME_TRIAL)p.state=V6_SAVE_PAGE_TIMETRIAL;
    else if(f&V6_SAVE_PAGE_SECRET_LAB)p.state=V6_SAVE_PAGE_SECRETLAB;
    else if(f&V6_SAVE_PAGE_ERROR)p.state=V6_SAVE_PAGE_FAILED;
    else {
        p.autosave_note=!(f&V6_SAVE_PAGE_CUSTOM);
        if(f&V6_SAVE_PAGE_SAVED)p.state=V6_SAVE_PAGE_RECEIPT;
        else p.last_summary=!(f&V6_SAVE_PAGE_CUSTOM) && (f&V6_SAVE_PAGE_LAST_EXISTS)!=0;
    }
    return p;
}
const char *v6_save_page_message(unsigned state)
{
    switch(state) {
    case V6_SAVE_PAGE_RECEIPT:return "Game saved ok!";
    case V6_SAVE_PAGE_REPLAY:return "Cannot Save in Level Replay";
    case V6_SAVE_PAGE_NODEATH:return "Cannot Save in No Death Mode";
    case V6_SAVE_PAGE_TIMETRIAL:return "How'd you get here?";
    case V6_SAVE_PAGE_SECRETLAB:return "Cannot Save in Secret Lab";
    case V6_SAVE_PAGE_FAILED:return "ERROR: Could not save game!";
    default:return 0; /* Prompt includes the platform's action binding. */
    }
}

int v6_save_page_unpack(uint8_t *out,const uint8_t *runs,unsigned bytes)
{
    unsigned i,total=0,n;
    if(!out || !runs || (bytes&1))return 0;
    for(i=0;i<bytes;i+=2) {
        if(!runs[i] || total>V6_SAVE_BITMAP_BYTES-runs[i])return 0;
        total+=runs[i];
    }
    if(total!=V6_SAVE_BITMAP_BYTES)return 0;
    for(i=0;i<bytes;i+=2)for(n=0;n<runs[i];++n)*(volatile uint8_t *)out++=runs[i+1];
    return 1;
}
