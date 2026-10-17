// GraphRAG course — Neo4j schema bootstrap
// Loaded manually after the container is up:
//   docker compose exec neo4j cypher-shell -u neo4j -p graphrag123 \
//     -f /init/neo4j_init.cypher
//
// This file is bind-mounted at /init (deliberately outside /var/lib/neo4j,
// which the Neo4j entrypoint chowns at every start). Because it is a
// single-file bind mount, re-create the container after editing it:
//   docker compose up -d --force-recreate neo4j
//
// The M06 and M07 modules generate compatible MERGE statements from the
// same data model, so the course labs and a live Neo4j instance stay aligned.

// ---------------------------------------------------------------------------
// 1. Constraints — entity identity and relationship identity
// ---------------------------------------------------------------------------

CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

// A relationship in the extracted graph is identified by (source, type, target).
// Neo4j still does not support composite uniqueness on relationships in
// Community Edition, so deduplication is enforced in the write path
// (MERGE on the endpoints) instead of by the database.

// ---------------------------------------------------------------------------
// 2. Indexes — lookup paths used by the GraphRAG retrieval patterns
// ---------------------------------------------------------------------------

CREATE INDEX entity_name_index IF NOT EXISTS
FOR (e:Entity) ON (e.name);

CREATE INDEX entity_type_index IF NOT EXISTS
FOR (e:Entity) ON (e.type);

CREATE INDEX chunk_doc_index IF NOT EXISTS
FOR (c:Chunk) ON (c.doc_id);

// Full-text index used for entity linking when the query string does not
// match a canonical entity name exactly (M07 — entity-anchored retrieval).
CREATE FULLTEXT INDEX entity_fulltext_index IF NOT EXISTS
FOR (e:Entity) ON EACH [e.name, e.aliases];

// ---------------------------------------------------------------------------
// 3. Sample data — same topology as the module labs
// ---------------------------------------------------------------------------

MERGE (aws:Entity:Provider {id: 'aws'})
  SET aws.name = 'Amazon Web Services',
      aws.aliases = ['AWS', 'amazon web services'];

MERGE (vpc:Entity:Network {id: 'vpc_prod'})
  SET vpc.name = 'VPC_Prod',
      vpc.aliases = ['vpc prod', 'production vpc'];

MERGE (gd:Entity:Service {id: 'guardduty'})
  SET gd.name = 'GuardDuty',
      gd.aliases = ['guard duty', 'amazon guardduty'];

MERGE (team:Entity:Team {id: 'secops'})
  SET team.name = 'SecOps_Team',
      team.aliases = ['security operations', 'secops'];

MERGE (doc:Document {id: 'doc_001'})
  SET doc.title = 'Cloud Security Architecture Overview',
      doc.source = 'sample';

MERGE (chunk:Chunk {id: 'doc_001#c0'})
  SET chunk.doc_id = 'doc_001',
      chunk.text = 'GuardDuty monitors VPC_Prod inside Amazon Web Services.';

// Relationships must be merged in a statement where both endpoints are already
// bound by MATCH. A bare `MERGE (chunk)-[:MENTIONS]->(gd)` in a new statement
// binds neither variable and silently creates two unlabeled nodes instead of
// connecting the ones created above.
MATCH (chunk:Chunk {id: 'doc_001#c0'}), (gd:Entity {id: 'guardduty'}),
      (vpc:Entity {id: 'vpc_prod'}), (aws:Entity {id: 'aws'}),
      (doc:Document {id: 'doc_001'}), (team:Entity {id: 'secops'})
MERGE (chunk)-[:MENTIONS]->(gd)
MERGE (chunk)-[:MENTIONS]->(vpc)
MERGE (chunk)-[:MENTIONS]->(aws)
MERGE (doc)-[:HAS_CHUNK]->(chunk)
MERGE (gd)-[:MONITORS]->(vpc)
MERGE (vpc)-[:HOSTED_ON]->(aws)
MERGE (gd)-[:MANAGED_BY]->(team);

// ---------------------------------------------------------------------------
// 4. Verification queries
// ---------------------------------------------------------------------------

// MATCH (n) RETURN labels(n) AS labels, count(*) AS n ORDER BY labels;
// MATCH (e:Entity)-[r]->(f:Entity) RETURN e.name, type(r), f.name ORDER BY e.name;
// CALL db.index.fulltext.queryNodes('entity_fulltext_index', 'guard')
//   YIELD node, score RETURN node.name, node.id, score;
// SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN *;
// -- note: Neo4j 5 removed the db.constraints() procedure; use SHOW CONSTRAINTS.
