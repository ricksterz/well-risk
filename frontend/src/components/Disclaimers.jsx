// Wording here is grounded in what the data and pipeline actually do (see
// classify.py, grid_join.py, and docs/deploy.md) - keep it in sync if those
// change. Deliberately avoids hardcoded counts so it doesn't go stale on
// each data refresh. Not reviewed by a lawyer; do that before relying on it
// for a commercial or high-traffic public launch.
const NOTICES = [
  {
    title: "Not an official classification",
    body: [
      "The risk tiers shown here (critical, high, medium, low, active, and unclassified) are this project's own judgment, made by grouping the status wording SONRIS publishes for each well. They are not an official determination, ranking, or risk score from any government agency, and no agency has reviewed or endorsed them. Tier boundaries are debatable, and different reasonable rules would sort some wells differently.",
      "This project is independent. It is not affiliated with, endorsed by, or sponsored by the State of Louisiana or the agency that publishes SONRIS.",
    ],
  },
  {
    title: "Where the data comes from, and how current it is",
    body: [
      "Well records come from the public SONRIS Office of Conservation map service and are copied in a batch when this site is built or redeployed. They are not live. Wells may since have been plugged, sold, reclassified, corrected, or added, and none of that appears here until the next refresh.",
      "SONRIS states that its own information is for general informational purposes only and that it makes no warranty of accuracy. This site inherits those limits and adds its own: the status wording in SONRIS is not always consistent (the same status can appear under different phrasings), so some wells may be sorted into the wrong tier or left unclassified.",
    ],
  },
  {
    title: "Orphan flags are history, not a current finding",
    body: [
      "In the source data, wells flagged as orphaned frequently show a current status of plugged and abandoned, or even producing, because the flag does not appear to be cleared when a well's status changes. This site therefore treats the flag as history and escalates a flagged well only while its current status is still unresolved.",
      "The meaning of the individual orphan status codes is not published, and this site does not interpret them.",
    ],
  },
  {
    title: "Locations are approximate and incomplete",
    body: [
      "Positions are the surface coordinates recorded in SONRIS. They can be imprecise, outdated, or missing, and some wells are recorded as unable to be located at all. Underground paths, such as deviated or horizontal wellbores, are not shown.",
      "The map is not a survey, plat, or site plan and must not be used to decide where to dig, drill, build, or buy. Before any ground disturbance, use the official one-call service (811) and consult the relevant records and qualified professionals.",
    ],
  },
  {
    title: "Flood and subsidence context is partial",
    body: [
      "Flood and subsidence context comes from FloodLens, a separate project whose coverage currently reaches only part of the study area: a minority of wells in Jefferson and Plaquemines parishes, and none in Lafourche.",
      "The “high risk in FloodLens coverage” figure counts only wells inside that coverage. It is not a count of all high-risk wells in flood-prone areas, and a well with no flood data has not been assessed, which is not the same as being safe. FloodLens scores are modeled estimates, not flood determinations or elevation certificates.",
    ],
  },
  {
    title: "Study area",
    body: [
      "Only wells recorded under Jefferson, Plaquemines, and Lafourche parishes are included, using the parish name recorded in SONRIS. Wells elsewhere, or recorded under a different parish name, are not shown, so a well's absence here does not mean there isn't one.",
    ],
  },
  {
    title: "Not professional advice",
    body: [
      "Everything here is for general information and education. It is not engineering, environmental, legal, financial, insurance, real estate, regulatory-compliance, or safety advice, and it should not be the basis for property transactions, underwriting, lending, litigation, remediation spending, or emergency decisions.",
      "A well shown as low or active has not been certified safe. A well shown as critical or high has not been inspected by this project, and its tier is not a finding of fault by or against any operator or landowner. Consult qualified professionals and the primary records.",
    ],
  },
  {
    title: "Names and records",
    body: [
      "Operator and well names are shown as recorded in SONRIS and may be outdated, misspelled, or attached to the wrong entity after sales and mergers. Their appearance here is not an allegation of wrongdoing.",
      "To correct a record, contact the agency that maintains SONRIS. Fixes will appear here only after the next data refresh.",
    ],
  },
  {
    title: "Third-party content",
    body: [
      "Map tiles and imagery are provided by Mapbox and OpenStreetMap contributors under their own terms. Third-party names and marks belong to their owners and are used only to identify them.",
    ],
  },
  {
    title: "No warranty; limitation of liability",
    body: [
      "This site is provided “as is” and “as available,” without warranties of any kind, express or implied, including accuracy, completeness, timeliness, or fitness for a particular purpose. To the fullest extent the law allows, the authors and operators of this site are not liable for any loss or damage arising from its use or from reliance on its content.",
      "If you need to rely on information about a specific well, verify it against the official SONRIS record first.",
    ],
  },
];

export default function Disclaimers() {
  return (
    <footer className="disclaimers" aria-labelledby="disclaimers-heading">
      <h2 id="disclaimers-heading">Important notices and disclaimers</h2>
      <p className="disclaimers-intro">
        This dashboard is an independent, informational project built from public records. Please read the notices
        below before relying on anything shown above.
      </p>
      <div className="disclaimers-grid">
        {NOTICES.map((notice) => (
          <section key={notice.title}>
            <h3>{notice.title}</h3>
            {notice.body.map((paragraph, i) => (
              <p key={i}>{paragraph}</p>
            ))}
          </section>
        ))}
      </div>
    </footer>
  );
}
