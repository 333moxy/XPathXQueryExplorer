from flask import Flask, render_template, request, jsonify
from lxml import etree
from saxonche import PySaxonProcessor

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    xml_data = request.form.get('xml', '')
    query = request.form.get('query', '')
    engine = request.form.get('engine', 'xpath')
    
    try:
        if engine == 'xpath':
            parser = etree.XMLParser(recover=True, remove_blank_text=False)
            tree = etree.fromstring(xml_data.encode('utf-8'), parser=parser)
            results = tree.xpath(query)
            
            output_data = []
            for res in results:
                if isinstance(res, etree._Element):
                    start = res.sourceline
                    snippet = etree.tostring(res, encoding='unicode', with_tail=False)
                    end = start + snippet.count('\n')
                    output_data.append({"content": snippet.strip(), "start": start, "end": end})
                else:
                    output_data.append({"content": str(res), "start": 1, "end": 1})
            return jsonify({"status": "success", "results": output_data})

        else:
            with PySaxonProcessor(license=False) as proc:
                xq_proc = proc.new_xquery_processor()

                input_node = proc.parse_xml(xml_text=xml_data)
                if input_node is None:
                    return jsonify({"status": "error", "message": "Could not parse source XML"}), 400

                xq_proc.set_context(xdm_item=input_node)
                xq_proc.set_query_content(query)
                xq_proc.set_property("!indent", "yes")
                result_str = xq_proc.run_query_to_string()
                
                display_result = result_str if result_str is not None else "<!-- No output returned from query -->"
                
                return jsonify({
                    "status": "success", 
                    "generated_xml": display_result
                })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)