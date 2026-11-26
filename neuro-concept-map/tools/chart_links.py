# Link each concept-map node to the preclerkship overview chart (and column) that teaches it.
import json, re, sys

NAMES = {
 "neuro-w13-02_2": "Spinal tracts and cerebellum", "neuro-w13-04_2": "Cerebellum and basal ganglia",
 "neuro-w13-06_2": "Spinal cord", "neuro-w13-07_2": "Neuro-ophthalmology", "neuro-w13-08_2": "Cortical syndromes",
 "neuro-w13-09_2": "Approach to weakness", "neuro-w13-10_2": "Approach to localization", "neuro-w13-13_2": "Neuroradiology",
 "neuro-w14-01_2": "Head injuries", "neuro-w14-02_2": "Multiple sclerosis", "neuro-w14-03_2": "Approach to stroke",
 "neuro-w14-04_2": "Sensory symptoms", "neuro-w14-05_2": "Neuropathic pain", "neuro-w14-06_2": "Approach to headache",
 "neuro-w14-07_2": "Altered level of consciousness", "neuro-w14-08_2": "Approach to seizures",
 "neuro-w14-10_2": "Neurosurgical emergencies", "neuro-w14-11_2": "Neuroinfections", "neuro-w15-02_2": "Brain tumours",
 "neuro-w15-03_2": "Movement disorders", "neuro-w15-04_2": "Non-Mendelian genetics", "neuro-w15-05_2": "The floppy infant",
 "neuro-w15-05_3": "The seizing child", "neuro-w15-05_4": "The ataxic child", "neuro-w15-06_2": "Monocular vision loss",
 "neuro-w15-07_2": "Red eye", "neuro-w15-07_3": "Ocular trauma", "neuro-w15-08_2": "Pediatric ophthalmology",
 "neuro-w15-09_2": "Hearing loss", "neuro-w15-10_2": "Vertigo", "neuro-w15-11_2": "Medicine and neurology",
}
R = [  # (pattern on the node title, chart suffix, column or None); first match wins, a second different chart may be added
 (r"cluster headache", "w14-06_2", "clu"), (r"tension headache", "w14-06_2", "tth"), (r"migraine", "w14-06_2", "mig"),
 (r"gca headache", "w14-06_2", "gca"), (r"meningitis headache", "w14-06_2", "men"), (r"sah headache", "w14-06_2", "sah"),
 (r"idiopathic intracranial hyper", "w14-06_2", "iih"), (r"icp headache \(", "w14-06_2", "tum"),
 (r"headache|intracranial hypotension", "w14-06_2", None),
 (r"brain death", "w14-07_2", "bd"), (r"^coma", "w14-07_2", "coma"), (r"vegetative", "w14-07_2", "vs"),
 (r"mcs \(−\)|minimally conscious", "w14-07_2", "mcsm"), (r"mcs \(\+\)|emergence from mcs", "w14-07_2", "mcsp"),
 (r"other alterations", "w14-07_2", "lis"),
 (r"altered level|disorders of consciousness|unconscious|mental status|cranial nerve pex|sensory/motor pex", "w14-07_2", None),
 (r"status epilepticus", "w14-08_2", "se"), (r"^epilepsy|primary \(seizures\)", "w14-08_2", "epi"),
 (r"provoked|seizure cause", "w14-08_2", "prov"), (r"first seizure", "w14-08_2", "single"),
 (r"syncope|transient loss|metabolic \(loc\)|less common causes \(loc\)|transient focal", "w14-08_2", "ne"),
 (r"simple febrile|febrile seizures", "w15-05_3", "sfs"), (r"complex febrile", "w15-05_3", "cfs"),
 (r"rash in ch", "w14-11_2", "bac"),
 (r"seizure|ictal", "w14-08_2", None),
 (r"bacterial meningitis", "w14-11_2", "bac"), (r"viral meningitis", "w14-11_2", "asep"),
 (r"encephalitis", "w14-11_2", "hsv"), (r"meningoencephalitis", "w14-11_2", None),
 (r"hydroceph", "w14-10_2", "hyd"), (r"herniation|monro|intracranial pressure|icp", "w14-10_2", None),
 (r"metasta", "w15-02_2", "met"), (r"glioblastoma|anaplastic", "w15-02_2", "hgg"), (r"low grade glioma", "w15-02_2", "lgg"),
 (r"lymphoma", "w15-02_2", "pcl"), (r"glioma|brain tumors", "w15-02_2", None), (r"paraneoplastic", "w15-11_2", "onc"),
 (r"epidural", "w14-01_2", "edh"), (r"subdural", "w14-01_2", "sdh"), (r"diffuse axonal", "w14-01_2", "dai"),
 (r"contusion", "w14-01_2", "cont"), (r"concussion", "w14-01_2", "conc"), (r"traumatic brain", "w14-01_2", None),
 (r"subarachnoid", "w14-03_2", "sah"), (r"intracerebral", "w14-03_2", "ich"), (r"hemorrhag", "w14-03_2", None),
 (r"transient ischemic", "w14-03_2", "tia"), (r"stroke|tpa|thrombolytic", "w14-03_2", "isch"),
 (r"multiple sclerosis", "w14-02_2", None),
 (r"wernicke-korsakoff|thiamine|beri", "w15-11_2", "wer"), (r"b12|nutritional", "w15-11_2", "nut"),
 (r"neuroradiology", "w13-13_2", None), (r"neurological disorders|cns focal lesion", "w13-10_2", None),
 (r"anterior cord", "w13-06_2", "ant"), (r"posterior cord", "w13-06_2", "post"), (r"central cord", "w13-06_2", "cent"),
 (r"séquard|sequard", "w13-06_2", "bs"), (r"cauda equina|severe lumbar", "w13-06_2", "ce"),
 (r"spinal nerve|radiculopathy|mild lumbar", "w13-06_2", "rad"),
 (r"dorsal column", "w13-02_2", "dcml"), (r"spinothalamic", "w13-02_2", "stt"), (r"corticospinal", "w13-02_2", "lcst"),
 (r"spinal cord tracts", "w13-02_2", None), (r"^spinal cord|quadripleg", "w13-09_2", "cord"), (r"hemipleg", "w13-09_2", "brain"),
 (r"broca", "w13-08_2", "broca"), (r"wernicke's aphasia", "w13-08_2", "wern"), (r"global aphasia", "w13-08_2", "glob"),
 (r"aphasia|apraxia|neglect|extinction|hemisphere|cortical sensory|sensory association|mca stroke", "w13-08_2", None),
 (r"cerebral cortex|frontal lobe \(1", "w13-10_2", "cortex"), (r"subcortical", "w13-10_2", "subcortex"),
 (r"brainstem|pons|medull|crossed|lower cns", "w13-10_2", "stem"),
 (r"anterior horn|amyotrophic", "w13-09_2", "ahc"), (r"plexus", "w13-09_2", "plex"),
 (r"neuromuscular junction|myasthenia", "w13-09_2", "nmj"), (r"muscles \(myopathy\)", "w13-09_2", "muscle"),
 (r"guillain", "w14-04_2", "gbs"),
 (r"polyneuropathy|polyradic|symmetrical & distal|large fiber|small fiber|diabetic neuropathy|sensory neuropathies|etiologies \(demy", "w14-04_2", "poly"),
 (r"peripheral nerve \(|mononeuro|asymmetrical distribution|neurotmesis|axonotmesis|neurapraxia", "w14-04_2", "mono"),
 (r"dorsal root ganglion", "w14-04_2", "root"),
 (r"neuropathic pain|nociceptive|crps|regional pain|sensitization", "w14-05_2", None),
 (r"myotonic", "w15-04_2", "dm"),
 (r"umn lesion \(infant|umn lesion etiologies|genetic|pre/perinatal|cerebral palsy", "w15-05_2", "cen"),
 (r"lmn lesion \(infant|lmn lesion etiologies", "w15-05_2", "per"),
 (r"hypotonia|floppy|children <3|mixed umn|non-neurologic", "w15-05_2", None),
 (r"umn lesion|lmn lesion|weakness|^localization$|motor-only|motor and sensory|myotome|other distribution", "w13-09_2", None),
 (r"horner|sympathetics", "w13-07_2", "symp"), (r"cn iii|oculomotor|compressive lesion|ischemic lesion", "w13-07_2", "cn3"),
 (r"cn iv|trochlear", "w13-07_2", "cn4"), (r"cn vi\b|abducens", "w13-07_2", "cn6"),
 (r"ptosis|diplopia|cn palsies|visual field|innervation of the eyes|cn ii\b|optic n\.", "w13-07_2", None),
 (r"central retinal|crao", "w15-06_2", "crao"), (r"giant cell", "w15-06_2", "gca"), (r"optic neuritis", "w15-06_2", "on"),
 (r"retinal detachment", "w15-06_2", "rd"), (r"chronic vision", "w15-06_2", "gl"),
 (r"monocular|amaurosis|ischemic optic|acute vision", "w15-06_2", None),
 (r"corneal abrasion", "w15-07_2", "abr"), (r"ocular trauma", "w15-07_3", None),
 (r"red eyes|vision threatening", "w15-07_2", None),
 (r"amblyopia", "w15-08_2", "amb"), (r"red reflex|leukokoria|retinoblastoma", "w15-08_2", "white"),
 (r"sensorineural", "w15-09_2", "ssnhl"), (r"untreated om|conductive", "w15-09_2", "om"), (r"hearing|cochlea", "w15-09_2", None),
 (r"vestibular dx|vertigo|nystagmus|semicircular|vor\b|vestibulo|utricle|saccades|vestibular nucleus", "w15-10_2", None),
 (r"dysarthria", "w13-10_2", "dys"),
 (r"cerebell|intention tremor", "w13-04_2", "cereb"),
 (r"essential tremor", "w15-03_2", "et"), (r"parkinson's disease|hypokinetic|l-dopa", "w15-03_2", "pd"),
 (r"other causes of parkinsonism|systems atrophy|supranuclear", "w15-03_2", "oth"), (r"tremor", "w15-03_2", None),
 (r"huntington", "w15-04_2", "hd"), (r"chorea|hyperkinetic|ballism|dyskinesia", "w13-04_2", "chor"),
 (r"basal ganglia|release inhibition", "w13-04_2", "pd"), (r"ataxia|romberg|gait", "w13-04_2", None),
]
BASE = "https://schulichmed.github.io/preclerkship/pom2/charts/"

def links_for(title):
    t = re.sub(r"<[^>]+>|📍", "", title).strip().lower()
    out = []
    for pat, ch, col in R:
        if re.search(pat, t):
            cid = "neuro-" + ch
            if any(o["chart"] == cid for o in out): continue
            out.append({"chart": cid, "col": col, "name": NAMES[cid], "url": BASE + cid + "/" + (f"#col={col}" if col else "")})
            if len(out) == 2: break
    return out

if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    n_with = 0; used = set()
    for n in data["nodes"]:
        n["charts"] = links_for(n["title"])
        if n["charts"]: n_with += 1
        used.update(c["chart"] for c in n["charts"])
    json.dump(data, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(n_with, "of", len(data["nodes"]), "nodes linked;", len(used), "of", len(NAMES), "charts used")
    print("unused charts:", sorted(set(NAMES) - used))
