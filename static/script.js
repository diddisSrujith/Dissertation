const margin = { top: 40, right: 200, bottom: 40, left: 120 };
const svgElement = d3.select("#main-tree");
const g = svgElement.append("g");
let root;
let viewMode = "combined";
async function loadWord(word) {
  const response = await fetch(`/extract/${word}`);
  const data = await response.json();
  const tree = data.tree;
  const lemma = tree.lemma || word;
  document.getElementById("welcome-message").style.display = "none";
  document.getElementById("graph-section").style.display = "block";
  document.title = `Etymology of ${lemma}`;
  document.getElementById("page-title").textContent =
    `Etymology of ${lemma}`;
  root = d3.hierarchy(tree);
  root.children?.forEach(collapse);
  update(root);
  loadParallel(data.parallel);
}
function collapse(d) {
  if (d.children) {
    d._children = d.children;
    d._children.forEach(collapse);
    d.children = null;
  }
}
function formatLabel(name) {
  if (viewMode === "combined") {
    return name;
  }
  const match = name.match(/^(.*?)\s*\((.*?)\)$/);
  if (!match) {
    return name;
  }
  const lang = match[1].trim();
  const words = match[2].trim();
  if (viewMode === "language") {
    return lang;
  }
  if (viewMode === "word") {
    return words;
  }
  return name;
}
function update(source) {
  const treeLayout = d3.tree().size([600, 900]);
  treeLayout(root);
  let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
  root.descendants().forEach(d => {
    if (d.x < minX) minX = d.x;
    if (d.x > maxX) maxX = d.x;
    if (d.y < minY) minY = d.y;
    if (d.y > maxY) maxY = d.y;
  });
  const width =
    maxY - minY + margin.left + margin.right;
  const height =
    maxX - minX + margin.top + margin.bottom;
  svgElement
    .attr("width", width)
    .attr("height", height);
  g.attr(
    "transform",
    `translate(${margin.left - minY},
               ${margin.top - minX})`
  );
  const link = g.selectAll(".link")
    .data(root.links(), d => d.target.data.name);
  link.enter()
    .append("path")
    .attr("class", "link")
    .merge(link)
    .attr("d",
      d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x)
    );
  link.exit().remove();
  const node = g.selectAll(".node")
    .data(root.descendants(), d => d.data.name);
  const nodeEnter = node.enter()
    .append("g")
    .attr("class", "node")
    .on("click", (event, d) => toggle(d));
  nodeEnter.append("circle")
    .attr("class", "node-glow")
    .attr("r", 10);
  nodeEnter.append("circle")
    .attr("class", "node-core")
    .attr("r", d => {
      if (d.depth === 0) return 7;
      if (d.depth === 1) return 5;
      return 4;
    });
  nodeEnter.append("text")
    .attr("x", 10)
    .attr("dy", "-0.6em")
    .each(renderText);
  nodeEnter.merge(node)
    .attr(
      "transform",
      d => `translate(${d.y},${d.x})`
    )
    .select("text")
    .each(renderText);
  nodeEnter.merge(node)
    .select(".node-glow")
    .style(
      "display",
      d => d._children ? "block" : "none"
    );
  node.exit().remove();
}
function renderText(d) {
  const text = d3.select(this);
  text.text("");
  const label = formatLabel(d.data.name);
  if (viewMode === "language") {
    text.append("tspan")
      .text(label)
      .attr("fill", "#1d4ed8");
    return;
  }
  if (viewMode === "word") {
    text.append("tspan")
      .text(label)
      .attr("fill", "#15803d");
    return;
  }
  const match =
    label.match(/^(.*?)\s*\((.*?)\)$/);
  if (!match) {
    text.append("tspan")
      .text(label)
      .attr("fill", "#111");
    return;
  }
  const lang = match[1].trim();
  const words = match[2].trim();
  text.append("tspan")
    .text(lang + " ")
    .attr("fill", "#1d4ed8");
  text.append("tspan")
    .text("(" + words + ")")
    .attr("fill", "#15803d");
}
function toggle(d) {
  if (d.children) {
    d._children = d.children;
    d.children = null;
  } else {
    d.children = d._children;
    d._children = null;
  }
  update(d);
}
function setView(mode, element) {
  viewMode = mode;
  document.querySelectorAll(".tab")
    .forEach(btn => {
      btn.classList.remove("active");
    });
  element.classList.add("active");
  if (!root) {
    return;
  }
  update(root);
}
const parallelSvg =
  d3.select("#parallel-tree");
const parallelGroup =
  parallelSvg.append("g")
    .attr("transform", "translate(120,40)");
function loadParallel(data) {
    parallelGroup.selectAll("*").remove();
    const parallelRoot =
      d3.hierarchy(data);
    const layout =
      d3.tree().size([250, 500]);
    layout(parallelRoot);
    parallelSvg
      .attr("width", 900)
      .attr("height", 350);
    parallelGroup.selectAll(".parallel-link")
      .data(parallelRoot.links())
      .enter()
      .append("path")
      .attr("fill","none")
      .attr("stroke","#94a3b8")
      .attr("stroke-width",1.5)
      .attr(
        "d",
        d3.linkHorizontal()
          .x(d=>d.y)
          .y(d=>d.x)
      );
    const node =
      parallelGroup.selectAll(".parallel-node")
        .data(parallelRoot.descendants())
        .enter()
        .append("g")
        .attr(
          "transform",
          d=>`translate(${d.y},${d.x})`
        );
    node.append("circle")
      .attr("r",d=>d.depth===0?7:5)
      .attr("fill","#7c3aed");
    node.append("text")
      .attr("x",10)
      .attr("dy","0.3em")
      .style("font-size","13px")
      .style("font-weight","600")
      .text(d=>d.data.name);
}
function buildSidebar() {
    const list = document.getElementById("word-list");
    list.innerHTML = "";
    WORDS.forEach((entry, index) => {
        const item = document.createElement("div");
        item.className = "word-item";
        item.textContent = entry.word;
        item.onclick = () => {
          document
              .querySelectorAll(".word-item")
              .forEach(x => x.classList.remove("active"));
          item.classList.add("active");
          // Do not display licensed source text
          document.getElementById("origin").value = "";
          document.getElementById("etymology").value = "";
          loadWord(entry.word);
      };
        list.appendChild(item);
        if (index === 0) {
            document.getElementById("page-title").textContent =
                "Etymology Explorer";

            document.title =
                "Etymology Explorer";
        }

    });
}
document
.getElementById("generate-btn")
.onclick = async () => {

    const origin =
        document.getElementById("origin").value;

    const etymology =
        document.getElementById("etymology").value;

    const response = await fetch(
        "/extract",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                word: "Custom",
                origin,
                etymology
            })
        }
    );

    const data = await response.json();

    document.getElementById("welcome-message").style.display = "none";
    document.getElementById("graph-section").style.display = "block";

    // Reset title for manually entered etymology
    document.title = "Etymology Explorer";
    document.getElementById("page-title").textContent =
        "Etymology Explorer";

    // Remove selected sidebar highlight
    document
        .querySelectorAll(".word-item")
        .forEach(item => item.classList.remove("active"));

    root = d3.hierarchy(data.tree);
    root.children?.forEach(collapse);
    update(root);
    loadParallel(data.parallel);
};
buildSidebar();

document
    .getElementById("sidebar-toggle")
    .onclick = () => {

        const sidebar =
            document.getElementById("sidebar");

        const button =
            document.getElementById("sidebar-toggle");

        sidebar.classList.toggle("collapsed");

        if (sidebar.classList.contains("collapsed")) {

            button.textContent = "▶";

            button.style.left = "0px";

        } else {

            button.textContent = "◀";

            button.style.left = "270px";

        }
    };

    // =========================
// WORD SEARCH
// =========================

document
    .getElementById("word-search")
    .addEventListener("input", function () {

        const query =
            this.value.toLowerCase();

        document
            .querySelectorAll(".word-item")
            .forEach(item => {

                const word =
                    item.textContent.toLowerCase();

                item.style.display =
                    word.includes(query)
                    ? "block"
                    : "none";
            });
    });