"""Update the mid-period report with newly verified facts."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "药学情报周报_2026-08-17_2026-08-24.html"

content = REPORT.read_text(encoding="utf-8")

# 1. Update highlights
old_highlights = '''      <ol class="highlights">
        <li>本期核验并新增入库 6 条药学信息化项目动态（3 条招标、3 条中标/成交），官方公告页均已逐条核验，另有 2 条政策动向上榜。</li>
        <li>县域医共体「集中审方中心 + 中心（云）药房」打包采购活跃：郴州北湖 140 万元（08-18 已开标）、贵州息烽 269 万元（08-25 开标）。</li>
        <li>政策：重庆规范整合 12 项药学类医疗服务价格项目（2026-09-10 执行），新增居家药学服务费；国家卫健委部署居民连续用药管理。</li>
        <li>竞品美康：以软件著作权单一来源锁定成都市第七人民医院合理用药软件维保（8.7 万元/年），同期药品目录智能匹配专利公开。</li>
        <li>竞品逸曜：一周两中标——绍兴市人民医院合理用药及临床药师系统维保 26.7 万元（评审 95.4 分）、南京鼓楼医院临床药物警戒智慧平台 41.8 万元。</li>
        <li>深圳龙岗中心医院社康前置审方系统二次招标（49.98 万元，08-21 开标），基层社康场景竞争继续。</li>
      </ol>'''

new_highlights = '''      <ol class="highlights">
        <li>本期累计核验并新增入库 11 条药学信息化项目动态与 3 条政策动态，官方公告页均已逐条核验。本次 08-21 更新新增 5 条事实（3 条项目、1 条政策、1 条竞品维保）。</li>
        <li>政策：三部门（国卫药政发〔2026〕20号）要求公立医疗机构 2 个月内完成用药目录更新，信息系统须对基本药物标识提示优先使用，处方审核和点评须将基本药物优先使用情况作为重点。</li>
        <li>县域医共体「集中审方中心 + 中心（云）药房」打包采购活跃：郴州北湖 140 万元（08-18 已开标）、贵州息烽 269 万元（08-25 开标）。</li>
        <li>竞品美康：以软件著作权单一来源锁定成都市第七人民医院合理用药软件维保（8.7 万元/年）；广水全市审方中心系统中标 179.98 万元（品牌美康）；华润滨湖双鹤合理用药维保由美康承接。</li>
        <li>竞品逸曜：一周两中标——绍兴市人民医院合理用药及临床药师系统维保 26.7 万元（评审 95.4 分）、南京鼓楼医院临床药物警戒智慧平台 41.8 万元。</li>
        <li>新增项目：运城市盐湖区医疗集团中心药房信息系统（二次）102.65 万元（09-10 开标）；贵州医科大三附院合理用药+PASS 维保（三次）3.5 万元/年（08-25 开标）。</li>
        <li>深圳龙岗中心医院社康前置审方系统二次招标（49.98 万元，08-21 开标），基层社康场景竞争继续。</li>
      </ol>'''

content = content.replace(old_highlights, new_highlights)

# 2. Add new policy card after the existing two policy cards
old_policy_end = '''        </div>
      </div>
    </section>

    <section id="regional-procurements">'''

new_policy_card = '''          <article class="card">
            <h4>三部门部署基本药物优先配备使用：信息系统须标识提示</h4>
            <p class="fact">国家卫生健康委、国家中医药局、国家疾控局联合发布《关于做好基本药物优先配备使用工作的通知》（国卫药政发〔2026〕20号，2026-08-19 成文）。要求各级公立医疗卫生机构在新版国家基本药物目录实施后 2 个月内完成用药供应目录更新调整；在信息系统中对基本药物进行标识，提示优先使用；将基本药物优先合理使用情况作为处方审核和点评的重点内容。紧密型医联体强化统一用药目录管理，调整周期原则上不超过 1 年。省级卫生健康行政部门须确定基本药物配备品种数量占比、使用量占比、金额占比及处方占比，并逐年提高。</p>
            <div class="sub">国家卫生健康委 · 国家中医药局 · 国家疾控局 · 国卫药政发〔2026〕20号 · 2026-08-19</div>
            <div class="tags">
              <span class="tag">基本药物</span>
              <span class="tag">信息系统标识</span>
              <span class="tag">处方审核点评</span>
              <span class="tag">医联体用药目录</span>
            </div>
            <p class="insight"><strong>对我方启发：</strong>基本药物信息系统标识、处方审核点评重点纳入、用药目录动态管理成为刚性要求，直接拉动 HIS/合理用药系统的目录管理与审方规则升级需求。</p>
            <div class="card-footer">
              <span class="status">wsjkw.hebei.gov.cn · ok（河北省卫健委官网转发全文核验）</span>
              <a class="btn" href="https://wsjkw.hebei.gov.cn/zcfg2/421156.jhtml" target="_blank" rel="noopener">🔗 来源</a>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section id="regional-procurements">'''

content = content.replace(old_policy_end, new_policy_card)

# 3. Add new rows to procurement table (before closing </tbody>)
old_table_end = '''          </tbody>
        </table>
      </div>
    </section>

    <section id="facts">'''

new_table_rows = '''            <tr>
              <td>湖北·广水</td>
              <td>中标（成交）结果公告</td>
              <td>广水市第一人民医院本级</td>
              <td>广水市第一人民医院全市审方中心系统购置项目（包括所有市直医疗机构、卫生院）</td>
              <td>全市审方中心系统、市直医疗机构及卫生院审方信息化</td>
              <td>中标179.98万元（预算190万元，评审96分）</td>
              <td>以原公告为准</td>
              <td>以原公告为准</td>
              <td>官方项目公告<br><a href="https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202608/t20260819_27163737.htm" target="_blank" rel="noopener">中国政府采购网</a></td>
            </tr><tr>
              <td>山西·运城</td>
              <td>公开招标（二次）</td>
              <td>运城市盐湖区医疗集团</td>
              <td>运城市盐湖区医疗集团中心药房信息系统采购项目（二次）</td>
              <td>医疗集团中心药房信息系统</td>
              <td>102.65万元</td>
              <td>2026-08-28（文件获取截止）</td>
              <td>2026-09-10 09:00</td>
              <td>官方项目公告<br><a href="https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202608/t20260820_27176882.htm" target="_blank" rel="noopener">中国政府采购网</a></td>
            </tr><tr>
              <td>贵州·都匀</td>
              <td>院内谈判（三次）</td>
              <td>贵州医科大学第三附属医院</td>
              <td>合理用药监测系统V4.3、PASS临床药学管理系统V.30维保项目（三次）</td>
              <td>合理用药监测系统V4.3、PASS临床药学管理系统V.30维保</td>
              <td>3.5万元/年（服务期3年）</td>
              <td>2026-08-24</td>
              <td>2026-08-25 10:00</td>
              <td>官方项目公告<br><a href="https://www.sfy-gmc.com/listitem.php?cid=4&amp;sid=31&amp;id=8074" target="_blank" rel="noopener">贵州医科大学第三附属医院官网</a></td>
            </tr><tr>
              <td>湖北·武汉</td>
              <td>单源直接采购</td>
              <td>武汉滨湖双鹤药业有限责任公司</td>
              <td>滨湖双鹤2026年合理用药系统维保采购项目</td>
              <td>合理用药系统维保</td>
              <td>未披露</td>
              <td>以原公告为准</td>
              <td>以原公告为准</td>
              <td>官方项目公告<br><a href="http://szecp.crc.com.cn/zbxx/006002/006002003/20260812/SHCJGG202608120006.html" target="_blank" rel="noopener">华润集团守正电子招标平台</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section id="facts">'''

content = content.replace(old_table_end, new_table_rows)

# 4. Add new fact cards before the medicom section
old_facts_end = '''    </section>

    <section id="medicom">'''

new_fact_cards = '''      <div class="group">
        <h3>药学信息化项目 · 湖北·广水</h3>
        <div class="grid">
        <article class="card">
          <h4>广水市第一人民医院全市审方中心系统购置项目</h4>
          <p class="fact">广水市第一人民医院全市审方中心系统购置项目（包括所有市直医疗机构、卫生院）中标成交公告。湖北乾讯网络科技有限公司以 179.98 万元中标（评审 96 分，预算 190 万元），品牌为四川美康（规格型号 V1）。项目覆盖全市审方中心系统及所有市直医疗机构、卫生院审方信息化，具体功能清单详见招标文件。</p>
          <div class="sub">中国政府采购网 · 湖北·广水 · 2026-08-19</div>
          <div class="tags">
            <span class="tag">审方中心</span>
            <span class="tag">全市覆盖</span>
            <span class="tag vendor">美康品牌</span>
            <span class="tag">处方审核</span>
          </div>
          <p class="insight"><strong>销售启发：</strong>全市审方中心覆盖市直+卫生院，区域审方平台型项目体量可观；美康以品牌方切入，需关注其区域审方方案的定价与交付模式。</p>
          <div class="card-footer">
            <span class="status">www.ccgp.gov.cn · ok</span>
            <a class="btn" href="https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202608/t20260819_27163737.htm" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>
        </div>
      </div>
      <div class="group">
        <h3>药学信息化项目 · 山西·运城</h3>
        <div class="grid">
        <article class="card">
          <h4>运城市盐湖区医疗集团中心药房信息系统采购项目（二次）</h4>
          <p class="fact">运城市盐湖区医疗集团就中心药房信息系统采购项目（二次）公开招标，预算及最高限价 102.65 万元，合同履约期自合同签订起 60 日历天交货。2026-08-21 至 2026-08-28 获取招标文件，2026-09-10 09:00 开标。专门面向中小企业采购。具体功能清单详见招标文件。</p>
          <div class="sub">中国政府采购网 · 山西·运城 · 2026-08-20</div>
          <div class="tags">
            <span class="tag">中心药房</span>
            <span class="tag">医疗集团</span>
            <span class="tag">二次招标</span>
            <span class="tag">中小企业</span>
          </div>
          <p class="insight"><strong>销售启发：</strong>二次招标项目需关注首次流标原因；医疗集团中心药房系统强调统一药品目录管理与上下级用药衔接能力。</p>
          <div class="card-footer">
            <span class="status">www.ccgp.gov.cn · ok</span>
            <a class="btn" href="https://www.ccgp.gov.cn/cggg/dfgg/gkzb/202608/t20260820_27176882.htm" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>
        </div>
      </div>
      <div class="group">
        <h3>药学信息化项目 · 贵州·都匀</h3>
        <div class="grid">
        <article class="card">
          <h4>贵州医科大学第三附属医院合理用药+PASS临床药学管理系统维保（三次）</h4>
          <p class="fact">贵州医科大学第三附属医院就合理用药监测系统 V4.3、PASS 临床药学管理系统 V.30 维保项目（三次）进行院内谈判采购，预算 3.5 万元/年，服务期 3 年（合同一年一签）。2026-08-24 报名截止，2026-08-25 10:00 开标。此前二次已废标。具体维保范围与需求详见招标文件附件。</p>
          <div class="sub">贵州医科大学第三附属医院官网 · 贵州·都匀 · 2026-08-20</div>
          <div class="tags">
            <span class="tag">合理用药</span>
            <span class="tag">PASS临床药学</span>
            <span class="tag">系统维保</span>
            <span class="tag">三次采购</span>
          </div>
          <p class="insight"><strong>销售启发：</strong>三次采购且此前废标，说明维保供应商衔接存在问题；可关注 PASS 系统维保市场的替代机会。</p>
          <div class="card-footer">
            <span class="status">www.sfy-gmc.com · ok</span>
            <a class="btn" href="https://www.sfy-gmc.com/listitem.php?cid=4&sid=31&id=8074" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>
        </div>
      </div>
    </section>

    <section id="medicom">'''

# Replace the FIRST occurrence of </section>\n\n    <section id="medicom">
# which is the end of the facts section
content = content.replace(old_facts_end, new_fact_cards, 1)

# 5. Update medicom section vendor note
old_medicom_note = '''      <p class="vendor-note">本周美康两条线并进：存量客户以「软件著作权 + 单一来源」锁定维保续约，同时药品目录智能匹配专利公开，知识库映射自动化与 AI 布局持续加码。</p>'''

new_medicom_note = '''      <p class="vendor-note">本周美康三线并进：存量客户以「软件著作权 + 单一来源」锁定维保续约（成都七院 8.7 万元、华润滨湖双鹤），同时以品牌方身份中标广水全市审方中心系统 179.98 万元；药品目录智能匹配专利公开，知识库映射自动化与 AI 布局持续加码。</p>'''

content = content.replace(old_medicom_note, new_medicom_note)

# 6. Add new medicom fact cards
old_medicom_grid_end = '''        </div>
      </div>
    </section>

    <section id="yiyao">'''

new_medicom_cards = '''        <article class="card">
          <h4>中标广水全市审方中心系统（品牌方身份，179.98 万元）</h4>
          <p class="fact">广水市第一人民医院全市审方中心系统购置项目（包括所有市直医疗机构、卫生院）中标成交公告，湖北乾讯网络科技有限公司以 179.98 万元中标（评审 96 分），品牌为四川美康（规格型号 V1）。美康以品牌方而非直接投标方身份切入全市审方中心项目，覆盖市直医疗机构及卫生院。</p>
          <div class="sub">中国政府采购网 · 湖北·广水 · 2026-08-19</div>
          <div class="tags">
            <span class="tag vendor">竞品中标</span>
            <span class="tag vendor">品牌方</span>
            <span class="tag">审方中心</span>
            <span class="tag">全市覆盖</span>
          </div>
          <p class="insight"><strong>销售启发：</strong>美康通过集成商/代理商以品牌方身份切入区域审方项目，模式可复制；需关注其区域审方方案的定价策略与代理商网络。</p>
          <div class="card-footer">
            <span class="status">www.ccgp.gov.cn · ok</span>
            <a class="btn" href="https://www.ccgp.gov.cn/cggg/dfgg/zbgg/202608/t20260819_27163737.htm" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>
        <article class="card">
          <h4>承接华润滨湖双鹤合理用药系统维保</h4>
          <p class="fact">华润集团守正电子招标平台公告，武汉滨湖双鹤药业有限责任公司 2026 年合理用药系统维保采购项目单源直接采购，供应商为四川美康医药软件研究开发股份有限公司。具体维保金额与服务期以原公告为准。</p>
          <div class="sub">华润集团守正电子招标平台 · 湖北·武汉 · 2026-08-12</div>
          <div class="tags">
            <span class="tag vendor">竞品维保</span>
            <span class="tag vendor">单源采购</span>
            <span class="tag">合理用药</span>
            <span class="tag">华润体系</span>
          </div>
          <p class="insight"><strong>销售启发：</strong>美康在华润体系内持续拓展维保客户，单源直接采购模式说明其合理用药系统在华润系医院有较高存量渗透率。</p>
          <div class="card-footer">
            <span class="status">szecp.crc.com.cn · ok</span>
            <a class="btn" href="http://szecp.crc.com.cn/zbxx/006002/006002003/20260812/SHCJGG202608120006.html" target="_blank" rel="noopener">🔗 来源</a>
          </div>
        </article>
        </div>
      </div>
    </section>

    <section id="yiyao">'''

content = content.replace(old_medicom_grid_end, new_medicom_cards, 1)

# 7. Update actions section
old_actions = '''      <div class="actions">
        <article class="action">
          <span class="priority">P0</span>
          <h3>跟进县域医共体「审方中心 + 中心药房」打包机会</h3>
          <p>郴州北湖项目 140 万元已于 08-18 开标，跟踪结果公告与采购人动态；息烽项目 269 万元 08-25 开标，仍在窗口期。两地均为医共体一体化打包，提前准备区域部署、多机构接口与快速交付方案。</p>
        </article>
        <article class="action">
          <span class="priority">P1</span>
          <h3>针对竞品维保锁定打出开放牌</h3>
          <p>美康、逸曜均以著作权/承建方身份形成单一来源维保锁定。在新项目与可替代机会中，突出开放接口、数据可迁移、规则库独立维护三项差异点，降低客户被锁定顾虑。</p>
        </article>
        <article class="action">
          <span class="priority">P1</span>
          <h3>提前布局药物警戒平台细分</h3>
          <p>南京鼓楼医院案例确认 ADR 监测智慧平台已成医院级独立采购标的（预算 50 万元档），逸曜已入局。建议梳理我方不良反应监测、智能上报与预警能力，形成可投标方案。</p>
        </article>
        <article class="action">
          <span class="priority">P2</span>
          <h3>产品话术对齐药学服务价格新政</h3>
          <p>重庆 12 项药学服务价格项目 09-10 执行，居家药学服务费、药学门诊诊查费落地。面向西南区域客户，将居家药学服务记录、药学门诊工作站等模块价值与收费项目直接对应。</p>
        </article>
      </div>'''

new_actions = '''      <div class="actions">
        <article class="action">
          <span class="priority">P0</span>
          <h3>对齐基本药物信息系统标识与审方点评要求</h3>
          <p>国卫药政发〔2026〕20号要求信息系统对基本药物标识提示优先使用、处方审核点评纳入基本药物优先使用情况。立即梳理我方合理用药系统的基药标识、审方规则与点评模板能力，形成合规升级方案。</p>
        </article>
        <article class="action">
          <span class="priority">P0</span>
          <h3>跟进县域医共体「审方中心 + 中心药房」打包机会</h3>
          <p>郴州北湖项目 140 万元已于 08-18 开标，跟踪结果公告与采购人动态；息烽项目 269 万元 08-25 开标，仍在窗口期。运城盐湖区中心药房 102.65 万元 09-10 开标。三地均为医共体/医疗集团一体化打包。</p>
        </article>
        <article class="action">
          <span class="priority">P1</span>
          <h3>应对美康品牌方+维保双线扩张</h3>
          <p>美康本周三线并进：成都七院维保锁定、广水审方中心品牌方中标 179.98 万元、华润滨湖双鹤维保承接。在区域审方与维保市场均形成攻势，需重点准备差异化竞争方案。</p>
        </article>
        <article class="action">
          <span class="priority">P1</span>
          <h3>提前布局药物警戒平台细分</h3>
          <p>南京鼓楼医院案例确认 ADR 监测智慧平台已成医院级独立采购标的（预算 50 万元档），逸曜已入局。建议梳理我方不良反应监测、智能上报与预警能力，形成可投标方案。</p>
        </article>
        <article class="action">
          <span class="priority">P2</span>
          <h3>产品话术对齐药学服务价格新政</h3>
          <p>重庆 12 项药学服务价格项目 09-10 执行，居家药学服务费、药学门诊诊查费落地。面向西南区域客户，将居家药学服务记录、药学门诊工作站等模块价值与收费项目直接对应。</p>
        </article>
      </div>'''

content = content.replace(old_actions, new_actions)

# 8. Update footer
old_footer = '''      数据流：官方公告核验 → 结构化事实表 weekly_report.json → HTML 渲染。本期新增入库 6 条项目事实与 2 条政策动态（均通过来源、日期、范围与去重校验）；未纳入纯药品采购内容；URL 无法访问或无法回到官方详情页的信息不进入本页。统计区间 2026-08-17 ~ 2026-08-24（中期发布），生成时间 2026-08-19 15:20（Asia/Shanghai）。'''

new_footer = '''      数据流：官方公告核验 → 结构化事实表 weekly_report.json → HTML 渲染。本期累计新增入库 11 条项目事实与 3 条政策动态（均通过来源、日期、范围与去重校验）；本次 08-21 更新新增 5 条事实；未纳入纯药品采购内容；URL 无法访问或无法回到官方详情页的信息不进入本页。统计区间 2026-08-17 ~ 2026-08-24，生成时间 2026-08-21 11:12（Asia/Shanghai）。'''

content = content.replace(old_footer, new_footer)

REPORT.write_text(content, encoding="utf-8")
print("Report updated successfully")
print(f"File size: {REPORT.stat().st_size} bytes")
