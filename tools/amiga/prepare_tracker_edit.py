#!/usr/bin/env python3
"""Freeze a verified eight-channel sketch as a non-overwriting edit handoff.

Only display names change in the editable MOD. Event locations are decoded
from its actual pattern cells and matched to the exported recognition events.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

CYCLES=(16,32,64,128,256)
ROLES=('bass','lead','harmony')


def sha(data):return hashlib.sha256(data).hexdigest()


def describe_module(data):
    if len(data)<1084 or data[1080:1084]!=b'8CHN':raise ValueError('expected an eight-channel MOD')
    length=data[950]
    if not 1<=length<=128:raise ValueError('invalid order list')
    orders=list(data[952:952+length]);patterns=max(data[952:1080])+1
    sample_offset=1084+patterns*2048;samples=[]
    for i in range(31):
        at=20+i*30;words,fine,volume,start,loop=struct.unpack_from('>HBBHH',data,at+22)
        if fine>15 or volume>64 or (loop>1 and start+loop>words):raise ValueError('invalid sample metadata')
        if i<15 and (words*2!=CYCLES[i%5] or start!=0 or loop!=words or fine!=1):
            raise ValueError('pitched sample bank differs from the verified sketch format')
        if words:
            entry=dict(number=i+1,hex=f'{i+1:02X}',name=data[at:at+22].rstrip(b'\0').decode('ascii'),bytes=words*2,finetune=fine if fine<8 else fine-16,loop_bytes=loop*2)
            if i<15:
                cycle=CYCLES[i%5];midi=round(69+12*math.log2(3546895/(428*cycle)/440))
                entry.update(role=ROLES[i//5],cycle=cycle,reference_period=428,reference_pitch=f'C{midi//12-1}',reference_midi=midi)
            else:entry.update(role='percussion')
            samples.append(entry)
    if len(data)!=sample_offset+sum(s['bytes'] for s in samples):raise ValueError('truncated or trailing MOD data')
    return dict(orders=orders,patterns=patterns,sample_offset=sample_offset,samples=samples)


def friendly_names(data):
    info=describe_module(data);result=bytearray(data)
    result[:20]=b'Positive Force edit'.ljust(20,b'\0')
    for sample in info['samples']:
        if sample['role']=='percussion':name=sample['name']
        else:name=f"{sample['role'].title()} {sample['reference_pitch']} P428"
        at=20+(sample['number']-1)*30;result[at:at+22]=name.encode('ascii')[:22].ljust(22,b'\0')
    return bytes(result)


def event_map(data,notes,arrangement,report,bpm=92):
    info=describe_module(data);starts={};step=7.5/bpm
    for order,pattern in enumerate(info['orders']):
        for row in range(64):
            for channel in range(7):
                at=1084+pattern*2048+row*32+channel*4
                a,b,c,volume=data[at:at+4];sample=(a&240)|(c>>4);period=(a&15)*256+b
                if not 1<=sample<=15 or not period:continue
                frequency=3546895/(period*CYCLES[(sample-1)%5])
                pitch=round(69+12*math.log2(frequency/440))
                key=(order*64+row,pitch,ROLES[(sample-1)//5])
                starts.setdefault(key,[]).append(dict(order=order,pattern=pattern,row=row,row_hex=f'{row:02X}',channel=channel+1,instrument=sample,instrument_hex=f'{sample:02X}',period=period,volume=volume))
    late={e['note_index']:e['actual_row'] for e in report['delayed_attacks']}
    missing=set(report['unstarted_note_indices']);result=[]
    for index,note in enumerate(notes):
        start,end,pitch,strength=note;planned=max(0,math.floor(start/step+.5));actual=late.get(index,planned)
        entry=dict(note_index=index,source_start=start,source_end=end,midi=pitch,confidence=strength,role=arrangement['roles'][index],planned_global_row=planned,vibrato=arrangement.get('vibrato',[None]*len(notes))[index])
        if index in missing:entry['status']='unstarted'
        else:
            key=(actual,pitch,arrangement['roles'][index]);matches=starts.get(key,[])
            if len(matches)!=1:raise ValueError(f'event {index} does not match one encoded attack')
            entry.update(matches.pop(),actual_global_row=actual,tracker_time=actual*step,status='delayed' if actual!=planned else 'started')
        result.append(entry)
    if any(matches for matches in starts.values()):raise ValueError('encoded attacks absent from note map')
    return result



def reduction_readiness(data,rows):
    """Count held pitched lanes, reserving one future music voice for drums.

    These role guesses are not independent musical parts. Foreground overlaps
    show where baking only harmony notes cannot meet a four-voice budget.
    """
    info=describe_module(data);lanes=[None]*7;profiles=[]
    if not 0<rows<=len(info['orders'])*64:raise ValueError('invalid played row count')
    for global_row in range(rows):
        order,row=divmod(global_row,64);pattern=info['orders'][order]
        for channel in range(7):
            at=1084+pattern*2048+row*32+channel*4
            a,b,c,value=data[at:at+4];sample=(a&240)|(c>>4)
            if 1<=sample<=15:lanes[channel]=ROLES[(sample-1)//5]
            if c&15==12 and value==0:lanes[channel]=None
        active=[role for role in lanes if role is not None]
        profiles.append(dict(pitched=len(active),foreground=sum(role in ('lead','bass') for role in active)))
    return dict(peak_pitched_voices=max(p['pitched'] for p in profiles),
        peak_foreground_voices=max(p['foreground'] for p in profiles),
        rows_over_four_voice_budget=sum(p['pitched']>3 for p in profiles),
        rows_over_three_voice_budget=sum(p['pitched']>2 for p in profiles),
        rows_requiring_more_than_harmony_baking=sum(p['foreground']>2 for p in profiles),
        played_rows=rows,assumption='One music voice reserved for percussion; other voices counted from held encoded pitched lanes. Foreground means provisional lead/bass roles; this is a capacity audit, not a reduction or native SFX policy.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('handoff directory already exists; choose a new path to protect manual edits')
    data=(a.baseline/'arranged-eight.mod').read_bytes();notes_bytes=(a.baseline/'notes.json').read_bytes()
    notes=json.loads(notes_bytes);arr=json.loads((a.baseline/'arrangement.json').read_text());report=json.loads((a.baseline/'report.json').read_text());replay=json.loads((a.baseline/'arranged-eight.render.json').read_text())
    if sha(data)!=report['sha256'] or sha(data)!=replay['module_sha256'] or sha(notes_bytes)!=arr['notes_sha256'] or sha(a.reference.read_bytes())!=arr['source_sha256']:p.error('baseline/reference provenance mismatch')
    if sha(a.library.read_bytes())!=replay['library_sha256']:p.error('replay library differs from verified baseline')
    if report['bpm']!=92 or report['replay_bpm']!=184 or report['replay_speed']!=6 or report['unstarted_note_indices']:p.error('handoff requires verified original-grid arrangement with every event started')
    try:
        editable=friendly_names(data);events=event_map(editable,notes,arr,report)
    except ValueError as error:p.error(str(error))
    info=describe_module(editable);row_seconds=7.5/92;markers=[]
    for time in (3,5,9,10,12,18):
        global_row=round(time/row_seconds);order,row=divmod(global_row,64)
        markers.append(dict(source_seconds=time,order=order,pattern=info['orders'][order],row=row,row_hex=f'{row:02X}',tracker_seconds=global_row*row_seconds))
    manifest=dict(version=1,title='Positive Force - first 24 seconds',baseline_module_sha256=sha(data),initial_editable_module_sha256=sha(editable),source_sha256=arr['source_sha256'],notes_sha256=sha(notes_bytes),
        accepted_for_manual_edit=True,reduction_readiness=reduction_readiness(editable,report['rows']),channels=8,editing_bpm=92,replay_bpm=184,replay_speed=6,row_seconds=row_seconds,instruments=info['samples'],reported_gap_markers=markers,
        known_delayed_events=[e for e in events if e['status']=='delayed'],existing_vibrato_events=[e for e in events if e['vibrato'] is not None],
        edit_policy='Editable MOD becomes authoritative after manual changes. Original JSON is recognition history, not synchronized with tracker edits. Initial hashes describe the handoff, not later edits.',
        scope='24-second editing prototype; not the complete track or native four-channel shipping asset')
    a.out.mkdir(parents=True)
    (a.out/'positive-force-edit.mod').write_bytes(editable);(a.out/'baseline.mod').write_bytes(data)
    (a.out/'notes.json').write_bytes(notes_bytes);(a.out/'arrangement.json').write_bytes((a.baseline/'arrangement.json').read_bytes());(a.out/'reference.wav').write_bytes(a.reference.read_bytes())
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(a.out/'event-map.json').write_text(json.dumps(events,indent=2)+'\n')
    from render_tracker import render
    rendered=render(a.library,a.out/'positive-force-edit.mod',a.out/'preview.wav')
    if (a.out/'preview.wav').read_bytes()!=(a.baseline/'arranged-eight.wav').read_bytes():raise ValueError('renamed module replay differs from verified baseline')
    (a.out/'preview.render.json').write_text(json.dumps(rendered,indent=2)+'\n')
    guide=['POSITIVE FORCE - MANUAL EDIT HANDOFF','',
        'Open positive-force-edit.mod in an editor supporting eight-channel 8CHN MOD.',
        'This is the first 24 seconds only. baseline.mod is the accepted unedited copy.',
        'preview.wav is the exact baseline replay; reference.wav is the original excerpt.',
        '', 'KEEP THE REPLAY CLOCK: BPM 184, speed 6. Each row is 81.522 ms.',
        '92 is the analysis grid, not the tempo to enter in the tracker.',
        'The source bar is approximately 1.714 s; pattern boundaries are editing blocks,',
        'not source bars. Preserve the initial F06 / FB8 commands and final B00 loop.',
        '', 'INSTRUMENTS (numbers shown in decimal / hex):',
        'Names state the approximate sounding C octave at period 428 (conventional C-2).',
        'Tracker octave labels vary. These are five tuning lengths per timbre, not',
        'five different instruments. Sample finetune remains +1 for pitched waves.']
    for sample in info['samples']:
        guide.append(f"{sample['number']:2d} / {sample['hex']}: {sample['name']}"+(' - '+sample['role'] if sample['role']=='percussion' else f" - {sample['cycle']} samples/cycle"))
    guide+=['','CHANNELS: 1-7 pitched notes; 8 drums. Held notes keep their lanes.',
        'Channels can carry different roles as voices spill. They are not fixed parts.',
        'Cxx sets volume; C00 releases. 4xy is calibrated vibrato at two events.',
        'EDx delays a drum attack within its row. B00 loops this excerpt.',
        '', 'REPORTED CORRECTION WINDOWS (order/pattern decimal, row hexadecimal):']
    for marker in markers:guide.append(f"{marker['source_seconds']:2d}s: order {marker['order']}, pattern {marker['pattern']}, row {marker['row_hex']} (near {marker['tracker_seconds']:.3f}s)")
    guide+=['','Known overload near 22.28s: one MIDI 68 attack waits from row 11 to 12',
        'in order/pattern 4. No event is completely lost by allocation.',
        'Residual work: missing notes, articulation, vibrato/arpeggios and percussion.',
        'Instrument identity/roles remain approximations; source drum timbres were',
        'accepted but rhythm still needs correction.',
        '', 'SAVE A NEW EDITED MOD. After editing, that MOD is authoritative.',
        'notes.json, arrangement.json and event-map.json describe this initial export;',
        'they do not update themselves when the tracker is edited. Re-exporting from',
        'those files would discard your tracker edits. This tool refuses an existing',
        'output directory. Preserve the unedited baseline for comparison.',
        '', 'Four-channel reduction/chord baking and native replay follow manual cleanup.',
        f"Current peak is {manifest['reduction_readiness']['peak_pitched_voices']} pitched voices plus the drum lane;",
        f"{manifest['reduction_readiness']['rows_requiring_more_than_harmony_baking']} rows have more than two foreground voices, so baking only",
        'harmony notes cannot guarantee a four-voice arrangement. Roles are provisional.',
        'This eight-channel asset is not an input for the four-channel hardware player.']
    (a.out/'README.txt').write_text('\n'.join(guide)+'\n')
    print(json.dumps(dict(output=str(a.out),events=len(events),module_sha256=sha(editable),replay_matches_baseline=True),indent=2))


if __name__=='__main__':main()
